import type { CvIngestionResponse, CvStructuredDataResponse } from "@/lib/api/types"

const API_URL = import.meta.env.VITE_API_URL

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string }
    if (body.detail) return body.detail
  } catch {
    // odpowiedź nie jest JSON-em — używamy statusText jako fallbacku
  }
  return response.statusText || `Żądanie zakończone błędem (${response.status})`
}

export async function uploadCv(file: File): Promise<CvIngestionResponse> {
  const formData = new FormData()
  formData.append("file", file)

  const response = await fetch(`${API_URL}/cv/upload`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status)
  }

  return (await response.json()) as CvIngestionResponse
}

export async function getCvStructured(cvDocumentId: string): Promise<CvStructuredDataResponse> {
  const response = await fetch(`${API_URL}/cv/${cvDocumentId}/structured`)

  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status)
  }

  return (await response.json()) as CvStructuredDataResponse
}
