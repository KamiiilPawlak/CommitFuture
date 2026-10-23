export interface CvIngestionResponse {
  message: string
  cv_document_id: string
  mime_type: string
  original_name: string
  character_count: number
  word_count: number
  raw_text: string
}

type CvStructuredStatus = "pending" | "completed" | "partial" | "failed"

type FieldSource = "heuristic" | "llm" | "merged"

interface WorkExperienceRecord {
  company: string | null
  role: string | null
  start_date: string | null
  end_date: string | null
  is_current: boolean
  responsibilities: string[]
  skills_used: string[]
}

interface HardSkillRecord {
  name: string
  months_used: number | null
  last_used: string | null
  source: FieldSource
}

interface SkillsRecord {
  hard: HardSkillRecord[]
  soft: string[]
  all_tech_stack_flat: string[]
}

interface EducationDto {
  institution: string | null
  degree: string | null
  field_of_study: string | null
  graduation_year: number | null
}

interface LanguageDto {
  language: string
  level: string | null
}

interface ValidationRecord {
  warnings: string[]
}

interface CvStructuredData {
  summary: string | null
  total_experience_months: number | null
  seniority_estimate: string | null
  work_experience: WorkExperienceRecord[]
  skills: SkillsRecord | null
  education: EducationDto[]
  languages: LanguageDto[]
  certifications: string[]
  validation: ValidationRecord | null
}

export interface CvStructuredDataResponse {
  cv_document_id: string
  status: CvStructuredStatus
  structured_data: CvStructuredData | null
  processed_at: string
}

export interface MatchRequest {
  cv_document_id: string
  job_posting_raw_text: string
}

export interface MatchResultResponse {
  overall_score: number
  seniority_match: boolean
  skill_coverage: number
  matched_skills: string[]
  missing_skills: string[]
  domain_overlap: string[]
  soft_skill_overlap: string[]
  education_match: boolean
}
