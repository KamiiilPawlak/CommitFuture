export interface CvIngestionResponse {
  message: string
  cv_document_id: string
  mime_type: string
  original_name: string
  character_count: number
  word_count: number
  raw_text: string
}

export type CvStructuredStatus = "pending" | "completed" | "partial" | "failed"

export type FieldSource = "heuristic" | "llm" | "merged"

export interface PersonalInfoRecord {
  full_name: string | null
  email: string | null
  phone: string | null
  location: string | null
  linkedin_url: string | null
}

export interface WorkExperienceRecord {
  company: string | null
  role: string | null
  start_date: string | null
  end_date: string | null
  is_current: boolean
  responsibilities: string[]
  skills_used: string[]
}

export interface HardSkillRecord {
  name: string
  months_used: number | null
  last_used: string | null
  source: FieldSource
}

export interface SkillsRecord {
  hard: HardSkillRecord[]
  soft: string[]
  all_tech_stack_flat: string[]
}

export interface EducationDto {
  institution: string | null
  degree: string | null
  field_of_study: string | null
  graduation_year: number | null
}

export interface LanguageDto {
  language: string
  level: string | null
}

export interface FieldConfidenceRecord {
  email: FieldSource | null
  phone: FieldSource | null
}

export interface ValidationRecord {
  warnings: string[]
  field_confidence: FieldConfidenceRecord
}

export interface CvStructuredData {
  cv_document_id: string | null
  status: string | null
  personal_info: PersonalInfoRecord | null
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
