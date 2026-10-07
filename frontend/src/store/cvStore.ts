import { create } from "zustand"

import { ApiError, getCvStructured, uploadCv } from "@/lib/api/client"
import type { CvStructuredDataResponse } from "@/lib/api/types"

type ResultEntry =
  | { status: "loading" }
  | { status: "success"; data: CvStructuredDataResponse }
  | { status: "error"; error: string }

interface CvStore {
  uploadStatus: "idle" | "uploading" | "error"
  uploadError: string | null
  results: Record<string, ResultEntry>
  upload: (file: File) => Promise<string>
  fetchResult: (cvDocumentId: string) => Promise<void>
}

function toMessage(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback
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

    set((state) => ({
      results: { ...state.results, [cvDocumentId]: { status: "loading" } },
    }))

    try {
      const data = await getCvStructured(cvDocumentId)
      set((state) => ({
        results: { ...state.results, [cvDocumentId]: { status: "success", data } },
      }))
    } catch (err) {
      const message = toMessage(err, "Nie udało się pobrać wyniku.")
      set((state) => ({
        results: { ...state.results, [cvDocumentId]: { status: "error", error: message } },
      }))
    }
  },
}))
