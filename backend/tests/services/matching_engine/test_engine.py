import pytest

from app.schema.matching_profile import (
    CandidateMatchingProfileDto,
    JobPostingMatchingDto,
    RequiredSkillDto,
    SkillMatchDto,
)
from app.services.matching_engine.engine import calculate_match


def _candidate(
    seniority: str = "mid",
    skills: list[str] | None = None,
    education_category: list[str] | None = None,
    domain_tags: list[str] | None = None,
    soft_skill_tags: list[str] | None = None,
) -> CandidateMatchingProfileDto:
    return CandidateMatchingProfileDto(
        seniority_level=seniority,
        total_experience_years=3.0,
        education_category=education_category or [],
        skills=[SkillMatchDto(name=skill) for skill in (skills or [])],
        domain_tags=domain_tags or [],
        soft_skill_tags=soft_skill_tags or [],
    )


def _job(
    min_seniority: str = "mid",
    required_skills: list[tuple[str, float]] | None = None,
    education_requirement: list[str] | None = None,
    nice_to_have_domain_tags: list[str] | None = None,
    soft_skill_tags: list[str] | None = None,
) -> JobPostingMatchingDto:
    return JobPostingMatchingDto(
        min_seniority=min_seniority,
        required_skills=[
            RequiredSkillDto(name=name, weight=weight)
            for name, weight in (required_skills or [])
        ],
        education_requirement=education_requirement or [],
        nice_to_have_domain_tags=nice_to_have_domain_tags or [],
        soft_skill_tags=soft_skill_tags or [],
    )


def test_full_skill_coverage_gives_perfect_skill_score() -> None:
    candidate = _candidate(skills=["python", "fastapi"])
    job = _job(required_skills=[("python", 1.0), ("fastapi", 1.0)])

    result = calculate_match(candidate, job)

    assert result.skill_coverage == 1.0
    assert result.matched_skills == ["fastapi", "python"]
    assert result.missing_skills == []


def test_zero_skill_coverage_gives_zero_skill_score() -> None:
    candidate = _candidate(skills=["java"])
    job = _job(required_skills=[("python", 1.0)])

    result = calculate_match(candidate, job)

    assert result.skill_coverage == 0.0
    assert result.matched_skills == []
    assert result.missing_skills == ["python"]


def test_partial_skill_coverage_is_between_zero_and_one() -> None:
    candidate = _candidate(skills=["python"])
    job = _job(required_skills=[("python", 1.0), ("kubernetes", 1.0)])

    result = calculate_match(candidate, job)

    assert 0.0 < result.skill_coverage < 1.0
    assert result.matched_skills == ["python"]
    assert result.missing_skills == ["kubernetes"]


def test_no_required_skills_counts_as_full_skill_coverage() -> None:
    candidate = _candidate(skills=["python"])
    job = _job(required_skills=[])

    result = calculate_match(candidate, job)

    assert result.skill_coverage == 1.0
    assert result.matched_skills == []
    assert result.missing_skills == []


def test_candidate_with_no_skills_against_required_skills_gives_zero_coverage() -> None:
    candidate = _candidate(skills=[])
    job = _job(required_skills=[("python", 1.0)])

    result = calculate_match(candidate, job)

    assert result.skill_coverage == 0.0
    assert result.missing_skills == ["python"]


@pytest.mark.parametrize(
    "candidate_level, min_level, expected",
    [
        ("junior", "mid", False),
        ("mid", "mid", True),
        ("senior", "mid", True),
        ("senior", "junior", True),
        ("junior", "senior", False),
    ],
)
def test_seniority_match_is_ordinal(
    candidate_level: str, min_level: str, expected: bool
) -> None:
    candidate = _candidate(seniority=candidate_level)
    job = _job(min_seniority=min_level)

    result = calculate_match(candidate, job)

    assert result.seniority_match is expected


def test_education_match_true_when_no_requirement() -> None:
    candidate = _candidate(education_category=[])
    job = _job(education_requirement=[])

    result = calculate_match(candidate, job)

    assert result.education_match is True


def test_education_match_true_on_category_overlap() -> None:
    candidate = _candidate(education_category=["computer_science"])
    job = _job(education_requirement=["computer_science", "mathematics"])

    result = calculate_match(candidate, job)

    assert result.education_match is True


def test_education_match_false_without_overlap() -> None:
    candidate = _candidate(education_category=["biology"])
    job = _job(education_requirement=["computer_science"])

    result = calculate_match(candidate, job)

    assert result.education_match is False


def test_domain_and_soft_skill_overlap_are_intersections() -> None:
    candidate = _candidate(
        domain_tags=["fintech", "healthcare"],
        soft_skill_tags=["ownership", "communication"],
    )
    job = _job(
        nice_to_have_domain_tags=["fintech", "ecommerce"],
        soft_skill_tags=["communication", "leadership"],
    )

    result = calculate_match(candidate, job)

    assert result.domain_overlap == ["fintech"]
    assert result.soft_skill_overlap == ["communication"]


def test_overall_score_rewards_full_match_on_every_dimension() -> None:
    candidate = _candidate(
        seniority="senior",
        skills=["python"],
        education_category=["computer_science"],
    )
    job = _job(
        min_seniority="senior",
        required_skills=[("python", 1.0)],
        education_requirement=["computer_science"],
    )

    result = calculate_match(candidate, job)

    assert result.overall_score == 100.0


def test_overall_score_is_zero_when_nothing_matches() -> None:
    candidate = _candidate(
        seniority="junior",
        skills=["java"],
        education_category=["biology"],
    )
    job = _job(
        min_seniority="senior",
        required_skills=[("python", 1.0)],
        education_requirement=["computer_science"],
    )

    result = calculate_match(candidate, job)

    assert result.overall_score == 0.0


def test_required_skill_weight_is_respected_in_coverage() -> None:
    candidate_full_weight = _candidate(skills=["python"])
    candidate_low_weight_job = _job(required_skills=[("python", 1.0)])
    high_weight_result = calculate_match(
        candidate_full_weight, candidate_low_weight_job
    )

    other_job = _job(
        required_skills=[("python", 1.0), ("rust", 1.0)],
    )
    diluted_result = calculate_match(candidate_full_weight, other_job)

    assert high_weight_result.skill_coverage > diluted_result.skill_coverage
