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

export interface WorkExperienceDto {
  company: string | null
  role: string | null
  start_date: string | null
  end_date: string | null
  responsibilities: string[]
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

export interface PersonalInfoDto {
  full_name: string | null
  email: string | null
  phone: string | null
  location: string | null
  linkedin_url: string | null
}

export interface ProjectDto {
  name: string
  description: string | null
  technologies: string[]
}

export interface CvLlmDto {
  personal_info: PersonalInfoDto
  summary: string | null
  hard_skills: string[]
  soft_skills: string[]
  work_experience: WorkExperienceDto[]
  projects: ProjectDto[]
  education: EducationDto[]
  languages: LanguageDto[]
  certifications: string[]
}

export interface DateRangeDto {
  start_date: string | null
  end_date: string | null
  is_current: boolean
}

export interface CvStructuredData {
  email: string | null
  phones: string[]
  dates: DateRangeDto[]
  tech_stack: string[]
  job_titles: string[]
  total_experience_months: number
  total_experience_years: number
  llm_result: CvLlmDto | null
  llm_warnings: string[]
  llm_hard_skills_validated: string[]
}

export interface CvStructuredDataResponse {
  cv_document_id: string
  status: CvStructuredStatus
  structured_data: CvStructuredData | null
  processed_at: string
}
