import pytest

from app.schema.cv_llm import WorkExperienceDto
from app.services.cv_pipeline.transform.dictionaries.validator import TechStackValidator
from app.services.cv_pipeline.transform.merge import (
    build_flat_tech_stack,
    build_unified_record,
    build_work_experience_entry,
    compute_skill_usage,
    estimate_seniority,
    is_current_role,
    resolve_field,
)


@pytest.fixture
def validator() -> TechStackValidator:
    return TechStackValidator()


@pytest.mark.parametrize(
    "end_date, expected",
    [
        (None, True),
        ("", True),
        ("Present", True),
        ("present", True),
        ("Obecnie", True),
        ("aktualnie", True),
        ("2022-01", False),
        ("2022", False),
    ],
)
def test_is_current_role(end_date: str | None, expected: bool) -> None:
    assert is_current_role(end_date) == expected


@pytest.mark.parametrize(
    "months, expected",
    [
        (0, "junior"),
        (23, "junior"),
        (24, "mid"),
        (71, "mid"),
        (72, "senior"),
        (300, "senior"),
    ],
)
def test_estimate_seniority_thresholds(months: int, expected: str) -> None:
    assert estimate_seniority(months) == expected


def test_resolve_field_agreeing_values_are_merged() -> None:
    value, source = resolve_field("a@test.com", "a@test.com", prefer="heuristic")
    assert value == "a@test.com"
    assert source == "merged"


def test_resolve_field_conflict_prefers_requested_source() -> None:
    value, source = resolve_field("a@test.com", "b@test.com", prefer="heuristic")
    assert value == "a@test.com"
    assert source == "heuristic"

    value, source = resolve_field("a@test.com", "b@test.com", prefer="llm")
    assert value == "b@test.com"
    assert source == "llm"


def test_resolve_field_one_sided_value() -> None:
    assert resolve_field(None, "b@test.com", prefer="heuristic") == ("b@test.com", "llm")
    assert resolve_field("a@test.com", None, prefer="heuristic") == (
        "a@test.com",
        "heuristic",
    )


def test_resolve_field_no_value() -> None:
    assert resolve_field(None, None, prefer="heuristic") == (None, "merged")


def test_build_work_experience_entry_present_role_has_null_end_date(
    validator: TechStackValidator,
) -> None:
    entry = WorkExperienceDto(
        company="Firma X",
        role="Python Developer",
        start_date="2020-01",
        end_date="Present",
        responsibilities=["Pisanie kodu"],
        skills_used=["python", "Docker "],
    )

    built = build_work_experience_entry(entry, validator)

    assert built["end_date"] is None
    assert built["is_current"] is True
    assert built["skills_used"] == ["docker", "python"]


def test_compute_skill_usage_merges_overlapping_ranges_per_skill(
    validator: TechStackValidator,
) -> None:
    work_experience = [
        WorkExperienceDto(
            company="A",
            role="Dev",
            start_date="2020-01",
            end_date="2022-01",
            skills_used=["Python", "Docker"],
        ),
        WorkExperienceDto(
            company="B",
            role="Lead Dev",
            start_date="2022-02",
            end_date=None,
            skills_used=["python", "Kubernetes"],
        ),
    ]

    usage = compute_skill_usage(work_experience, validator)

    assert usage["python"]["months_used"] > usage["docker"]["months_used"]
    assert usage["docker"]["last_used"] == "2022"
    assert usage["kubernetes"]["last_used"] != "2022"


def test_compute_skill_usage_ignores_unparseable_dates(
    validator: TechStackValidator,
) -> None:
    work_experience = [
        WorkExperienceDto(
            company="A", role="Dev", start_date=None, end_date=None, skills_used=["Python"]
        ),
    ]

    assert compute_skill_usage(work_experience, validator) == {}


def test_build_flat_tech_stack_dedupes_across_sources(
    validator: TechStackValidator,
) -> None:
    result = build_flat_tech_stack(["python", "docker"], ["Python", "Kubernetes"], validator)

    assert result == ["docker", "kubernetes", "python"]


def test_build_unified_record_without_llm_result_is_heuristic_only(
    validator: TechStackValidator,
) -> None:
    heuristic_result = {
        "email": "jan@test.com",
        "phones": ["+48123456789"],
        "dates": [],
        "tech_stack": ["Python"],
        "job_titles": ["Python Developer"],
        "total_experience_months": 10,
        "total_experience_years": 0.8,
    }

    record = build_unified_record(
        heuristic_result=heuristic_result,
        llm_result=None,
        llm_warnings=[],
        validated_hard_skills=[],
        validator=validator,
    )

    assert record["personal_info"]["email"] == "jan@test.com"
    assert record["personal_info"]["full_name"] is None
    assert record["work_experience"] == []
    assert record["seniority_estimate"] == "junior"
    assert record["skills"]["all_tech_stack_flat"] == ["python"]
    assert record["validation"]["field_confidence"]["email"] == "heuristic"
