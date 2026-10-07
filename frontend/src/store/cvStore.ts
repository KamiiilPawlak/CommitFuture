import { create } from "zustand"

import { ApiError, getCvStructured, uploadCv } from "@/lib/api/client"
import type { CvStructuredDataResponse } from "@/lib/api/types"

type ResultEntry =
  | { status: "loading" }
  | { status: "pending" }
  | { status: "success"; data: CvStructuredDataResponse }
  | { status: "error"; error: string }

interface CvStore {
  uploadStatus: "idle" | "uploading" | "error"
  uploadError: string | null
  results: Record<string, ResultEntry>
  upload: (file: File) => Promise<string>
  fetchResult: (cvDocumentId: string) => Promise<void>
  stopPolling: (cvDocumentId: string) => void
}

function toMessage(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback
}

// Przetwarzanie CV (OCR + LLM) trwa w tle, więc wynik "pending" jest doszukiwany
// ponownie co kilka sekund, aż backend zwróci status końcowy.
const POLL_INTERVAL_MS = 3000
const POLL_MAX_ATTEMPTS = 100 // ~5 minut

const pollTimers: Record<string, ReturnType<typeof setTimeout>> = {}

function clearPollTimer(cvDocumentId: string): void {
  const timer = pollTimers[cvDocumentId]
  if (timer) {
    clearTimeout(timer)
    delete pollTimers[cvDocumentId]
  }
}

export const useCvStore = create<CvStore>((set, get) => ({
  uploadStatus: "idle",
  uploadError: null,
  results: {},

  upload: async (file) => {
    set({ uploadStatus: "uploading", uploadError: null })

    try {
      const result = await uploadCv(file)
      set({ uploadStatus: "idle" })
      return result.cv_document_id
    } catch (err) {
      const message = toMessage(err, "Nie udało się przesłać pliku.")
      set({ uploadStatus: "error", uploadError: message })
      throw err
    }
  },

  fetchResult: async (cvDocumentId) => {
    if (get().results[cvDocumentId]?.status === "loading") return
    clearPollTimer(cvDocumentId)

    set((state) => ({
      results: { ...state.results, [cvDocumentId]: { status: "loading" } },
    }))

    const scheduleRetry = (attempt: number) => {
      if (attempt >= POLL_MAX_ATTEMPTS) {
        set((state) => ({
          results: {
            ...state.results,
            [cvDocumentId]: {
              status: "error",
              error:
                "Przetwarzanie CV trwa dłużej niż oczekiwano. Spróbuj odświeżyć stronę później.",
            },
          },
        }))
        return
      }
      pollTimers[cvDocumentId] = setTimeout(() => void poll(attempt + 1), POLL_INTERVAL_MS)
    }

    const poll = async (attempt: number) => {
      try {
        const data = await getCvStructured(cvDocumentId)

        if (data.status === "pending") {
          set((state) => ({ results: { ...state.results, [cvDocumentId]: { status: "pending" } } }))
          scheduleRetry(attempt)
          return
        }

        set((state) => ({
          results: { ...state.results, [cvDocumentId]: { status: "success", data } },
        }))
        clearPollTimer(cvDocumentId)
      } catch (err) {
        // Rekord pojawia się dopiero po zakończeniu przetwarzania w tle,
        // więc 404 na starcie oznacza "jeszcze nie gotowe", a nie błąd.
        if (err instanceof ApiError && err.status === 404) {
          set((state) => ({ results: { ...state.results, [cvDocumentId]: { status: "pending" } } }))
          scheduleRetry(attempt)
          return
        }

        const message = toMessage(err, "Nie udało się pobrać wyniku.")
        set((state) => ({
          results: { ...state.results, [cvDocumentId]: { status: "error", error: message } },
        }))
        clearPollTimer(cvDocumentId)
      }
    }

    await poll(0)
  },

  stopPolling: (cvDocumentId) => {
    clearPollTimer(cvDocumentId)
  },
}))
