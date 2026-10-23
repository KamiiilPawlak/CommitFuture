import type { MatchResultResponse } from "@/lib/api/types"

export const seedMatchResultHigh: MatchResultResponse = {
  overall_score: 82,
  seniority_match: true,
  skill_coverage: 78,
  matched_skills: ["TypeScript", "React", "Docker", "PostgreSQL"],
  missing_skills: ["Kubernetes"],
  domain_overlap: ["Fintech"],
  soft_skill_overlap: ["Komunikacja", "Praca w zespole"],
  education_match: true,
}

export const seedMatchResultLow: MatchResultResponse = {
  overall_score: 34,
  seniority_match: false,
  skill_coverage: 20,
  matched_skills: ["JavaScript"],
  missing_skills: ["Python", "AWS", "Terraform"],
  domain_overlap: [],
  soft_skill_overlap: [],
  education_match: false,
}
