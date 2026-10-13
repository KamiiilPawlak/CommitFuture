from app.services.job_pipline.transform.parse_job_posting import parse_job_posting

JOB_POSTING_TEXT = """
Senior Python Developer

Requirements:
- 5+ years of experience with Python and FastAPI
- Strong knowledge of PostgreSQL and Docker
- Experience with Kubernetes is a must

Responsibilities:
- Building microservices in Python and React
- Working with AWS infrastructure

Nice to have:
- Experience with GraphQL
- Knowledge of Rust

We are looking for someone with a Computer Science degree who has excellent
communication skills and takes ownership of their work.
"""


def test_parse_job_posting_detects_seniority_from_title() -> None:
    result = parse_job_posting(JOB_POSTING_TEXT)

    assert result.min_seniority == "senior"


def test_parse_job_posting_detects_junior_seniority() -> None:
    text = "Junior Backend Developer wanted, no experience required."

    result = parse_job_posting(text)

    assert result.min_seniority == "junior"


def test_parse_job_posting_defaults_to_mid_without_seniority_keywords() -> None:
    text = "Backend Developer wanted, Python and Docker required."

    result = parse_job_posting(text)

    assert result.min_seniority == "mid"


def test_parse_job_posting_assigns_full_weight_to_requirements_skills() -> None:
    result = parse_job_posting(JOB_POSTING_TEXT)

    skills_by_name = {skill.name: skill.weight for skill in result.required_skills}

    assert skills_by_name["python"] == 1.0
    assert skills_by_name["fastapi"] == 1.0
    assert skills_by_name["postgresql"] == 1.0
    assert skills_by_name["kubernetes"] == 1.0


def test_parse_job_posting_assigns_partial_weight_to_responsibilities_only_skills() -> (
    None
):
    result = parse_job_posting(JOB_POSTING_TEXT)

    skills_by_name = {skill.name: skill.weight for skill in result.required_skills}

    assert skills_by_name["react"] == 0.6


def test_parse_job_posting_excludes_nice_to_have_only_skills() -> None:
    result = parse_job_posting(JOB_POSTING_TEXT)

    skill_names = {skill.name for skill in result.required_skills}

    assert "graphql" not in skill_names
    assert "rust" not in skill_names


def test_parse_job_posting_extracts_soft_skill_tags() -> None:
    result = parse_job_posting(JOB_POSTING_TEXT)

    assert "ownership" in result.soft_skill_tags
    assert "communication" in result.soft_skill_tags


def test_parse_job_posting_extracts_education_requirement() -> None:
    result = parse_job_posting(JOB_POSTING_TEXT)

    assert "Computer Science" in result.education_requirement


def test_parse_job_posting_without_sections_treats_whole_text_as_requirements() -> None:
    text = "We need Python and Docker experience."

    result = parse_job_posting(text)

    skill_names = {skill.name for skill in result.required_skills}
    assert {"python", "docker"} <= skill_names
    assert all(skill.weight == 1.0 for skill in result.required_skills)


def test_parse_job_posting_empty_text_returns_default_profile() -> None:
    result = parse_job_posting("")

    assert result.min_seniority == "mid"
    assert result.required_skills == []
    assert result.nice_to_have_domain_tags == []
    assert result.education_requirement == []
    assert result.soft_skill_tags == []


def test_parse_job_posting_whitespace_only_text_returns_default_profile() -> None:
    result = parse_job_posting("   \n\t  ")

    assert result.min_seniority == "mid"
    assert result.required_skills == []
