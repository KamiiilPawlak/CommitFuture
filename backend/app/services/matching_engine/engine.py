import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.schema.matching_profile import (
    CandidateMatchingProfileDto,
    JobPostingMatchingDto,
    MatchResultDto,
    SeniorityLevel,
)

_SENIORITY_RANK: dict[SeniorityLevel, int] = {"junior": 0, "mid": 1, "senior": 2}

_SKILL_WEIGHT = 0.6
_SENIORITY_WEIGHT = 0.25
_EDUCATION_WEIGHT = 0.15


def _seniority_match(
    candidate_level: SeniorityLevel, min_level: SeniorityLevel
) -> bool:
    return _SENIORITY_RANK[candidate_level] >= _SENIORITY_RANK[min_level]


def _skill_cosine_similarity(
    candidate_skill_names: frozenset[str], job_posting: JobPostingMatchingDto
) -> float:
    if not job_posting.required_skills:
        return 1.0

    vocabulary = sorted(
        candidate_skill_names | {skill.name for skill in job_posting.required_skills}
    )

    candidate_vector = np.array(
        [1.0 if skill in candidate_skill_names else 0.0 for skill in vocabulary]
    ).reshape(1, -1)

    weight_per_skill = {
        skill.name: skill.weight for skill in job_posting.required_skills
    }
    job_vector = np.array(
        [weight_per_skill.get(skill, 0.0) for skill in vocabulary]
    ).reshape(1, -1)

    if not np.any(candidate_vector) or not np.any(job_vector):
        return 0.0

    return float(cosine_similarity(candidate_vector, job_vector)[0][0])


def _matched_missing_skills(
    candidate_skill_names: frozenset[str], job_posting: JobPostingMatchingDto
) -> tuple[list[str], list[str]]:
    required_names = {skill.name for skill in job_posting.required_skills}
    matched = sorted(required_names & candidate_skill_names)
    missing = sorted(required_names - candidate_skill_names)
    return matched, missing


def _education_match(
    candidate: CandidateMatchingProfileDto, job_posting: JobPostingMatchingDto
) -> bool:
    if not job_posting.education_requirement:
        return True
    return bool(
        set(candidate.education_category) & set(job_posting.education_requirement)
    )


def calculate_match(
    candidate: CandidateMatchingProfileDto, job_posting: JobPostingMatchingDto
) -> MatchResultDto:
    candidate_skill_names = frozenset(skill.name for skill in candidate.skills)

    seniority_match = _seniority_match(
        candidate.seniority_level, job_posting.min_seniority
    )
    skill_coverage = _skill_cosine_similarity(candidate_skill_names, job_posting)
    matched_skills, missing_skills = _matched_missing_skills(
        candidate_skill_names, job_posting
    )
    education_match = _education_match(candidate, job_posting)

    domain_overlap = sorted(
        set(candidate.domain_tags) & set(job_posting.nice_to_have_domain_tags)
    )
    soft_skill_overlap = sorted(
        set(candidate.soft_skill_tags) & set(job_posting.soft_skill_tags)
    )

    overall_score = 100.0 * (
        _SKILL_WEIGHT * skill_coverage
        + _SENIORITY_WEIGHT * (1.0 if seniority_match else 0.0)
        + _EDUCATION_WEIGHT * (1.0 if education_match else 0.0)
    )

    return MatchResultDto(
        overall_score=round(overall_score, 1),
        seniority_match=seniority_match,
        skill_coverage=round(skill_coverage, 3),
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        domain_overlap=domain_overlap,
        soft_skill_overlap=soft_skill_overlap,
        education_match=education_match,
    )
