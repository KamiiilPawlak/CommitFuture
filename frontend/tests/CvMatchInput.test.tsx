import { act, fireEvent, render, screen, waitFor } from "@testing-library/react"

import { CvMatchInput } from "@/components/CvMatchInput"
import { matchCv } from "@/lib/api/client"
import { useCvStore } from "@/store/cvStore"
import type { MatchResultResponse } from "@/lib/api/types"

jest.mock("@/lib/api/client", () => ({
  ApiError: class ApiError extends Error {
    status: number
    constructor(message: string, status: number) {
      super(message)
      this.status = status
    }
  },
  matchCv: jest.fn(),
}))

jest.mock("@/store/cvStore", () => ({
  useCvStore: jest.fn(),
}))

function createPdfFile(name = "cv.pdf") {
  return new File(["%PDF-1.4"], name, { type: "application/pdf" })
}

function getFileInput() {
  return document.querySelector('input[type="file"]') as HTMLInputElement
}

function fillJobDescription(text: string) {
  fireEvent.change(screen.getByPlaceholderText("Wklej tutaj treść ogłoszenia o pracę..."), {
    target: { value: text },
  })
}

const mockedUseCvStore = useCvStore as unknown as jest.Mock
const mockedMatchCv = matchCv as jest.Mock

interface MockCvResult {
  status: "loading" | "pending" | "success" | "error"
  error?: string
}

function setStoreState(overrides: { upload: jest.Mock; fetchResult: jest.Mock }) {
  const state: {
    results: Record<string, MockCvResult>
    upload: jest.Mock
    fetchResult: jest.Mock
  } = {
    results: {},
    upload: overrides.upload,
    fetchResult: overrides.fetchResult,
  }
  mockedUseCvStore.mockImplementation((selector: (s: typeof state) => unknown) => selector(state))
  return state
}

describe("CvMatchInput", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders the job description textarea and dropzone prompt", () => {
    setStoreState({ upload: jest.fn(), fetchResult: jest.fn() })
    render(<CvMatchInput onMatchResult={jest.fn()} />)

    expect(
      screen.getByPlaceholderText("Wklej tutaj treść ogłoszenia o pracę..."),
    ).toBeInTheDocument()
    expect(screen.getByText("Upuść plik PDF tutaj lub kliknij, aby wybrać")).toBeInTheDocument()
    expect(screen.getByText("Tylko pliki PDF")).toBeInTheDocument()
  })

  it("disables the matching button until a file and a job description are both present", async () => {
    setStoreState({ upload: jest.fn(), fetchResult: jest.fn() })
    render(<CvMatchInput onMatchResult={jest.fn()} />)

    const button = screen.getByRole("button", { name: "Rozpocznij matchowanie" })
    expect(button).toBeDisabled()

    fillJobDescription("Szukamy programisty")
    expect(button).toBeDisabled()

    await act(async () => {
      fireEvent.change(getFileInput(), { target: { files: [createPdfFile()] } })
    })

    expect(button).toBeEnabled()
  })

  it("shows the selected file after a PDF is dropped and allows removing it", async () => {
    setStoreState({ upload: jest.fn(), fetchResult: jest.fn() })
    render(<CvMatchInput onMatchResult={jest.fn()} />)

    const file = createPdfFile()
    await act(async () => {
      fireEvent.change(getFileInput(), { target: { files: [file] } })
    })

    expect(await screen.findByText("cv.pdf")).toBeInTheDocument()
    expect(
      screen.queryByText("Upuść plik PDF tutaj lub kliknij, aby wybrać"),
    ).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: /Usuń plik/ }))

    expect(screen.queryByText("cv.pdf")).not.toBeInTheDocument()
    expect(screen.getByText("Upuść plik PDF tutaj lub kliknij, aby wybrać")).toBeInTheDocument()
  })

  it("uploads the CV, waits for processing to finish, runs the match and reports the result", async () => {
    const result: MatchResultResponse = {
      overall_score: 80,
      seniority_match: true,
      skill_coverage: 70,
      matched_skills: ["React"],
      missing_skills: [],
      domain_overlap: [],
      soft_skill_overlap: [],
      education_match: true,
    }

    const upload = jest.fn().mockResolvedValue("doc-1")
    const fetchResult = jest.fn()
    const onMatchResult = jest.fn()
    mockedMatchCv.mockResolvedValue(result)

    const state = setStoreState({ upload, fetchResult })

    const { rerender } = render(<CvMatchInput onMatchResult={onMatchResult} />)

    fillJobDescription("Szukamy programisty")
    await act(async () => {
      fireEvent.change(getFileInput(), { target: { files: [createPdfFile()] } })
    })

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Rozpocznij matchowanie" }))
    })

    expect(upload).toHaveBeenCalledWith(expect.any(File))
    expect(fetchResult).toHaveBeenCalledWith("doc-1")
    expect(screen.getByRole("button", { name: "Matchowanie..." })).toBeDisabled()

    // Symulujemy zakończenie przetwarzania CV przez Celery, które cvStore
    // odkryłby przy kolejnym pollu — tu podstawiamy wynik ręcznie.
    state.results["doc-1"] = { status: "success" }
    rerender(<CvMatchInput onMatchResult={onMatchResult} />)

    await waitFor(() =>
      expect(mockedMatchCv).toHaveBeenCalledWith({
        cv_document_id: "doc-1",
        job_posting_raw_text: "Szukamy programisty",
      }),
    )
    await waitFor(() => expect(onMatchResult).toHaveBeenCalledWith(result))
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Rozpocznij matchowanie" })).toBeEnabled(),
    )
  })

  it("shows an error message when the CV upload fails", async () => {
    const { ApiError } = jest.requireMock("@/lib/api/client") as { ApiError: typeof Error }
    const upload = jest.fn().mockRejectedValue(new ApiError("Serwer niedostępny", 500))
    const fetchResult = jest.fn()
    setStoreState({ upload, fetchResult })

    render(<CvMatchInput onMatchResult={jest.fn()} />)

    fillJobDescription("Szukamy programisty")
    await act(async () => {
      fireEvent.change(getFileInput(), { target: { files: [createPdfFile()] } })
    })

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Rozpocznij matchowanie" }))
    })

    expect(await screen.findByText("Serwer niedostępny")).toBeInTheDocument()
    expect(fetchResult).not.toHaveBeenCalled()
  })
})
