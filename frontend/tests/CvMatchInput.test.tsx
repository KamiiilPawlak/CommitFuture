import { act, fireEvent, render, screen } from "@testing-library/react"

import { CvMatchInput } from "@/components/CvMatchInput"

function createPdfFile(name = "cv.pdf") {
  return new File(["%PDF-1.4"], name, { type: "application/pdf" })
}

function getFileInput() {
  return document.querySelector('input[type="file"]') as HTMLInputElement
}

describe("CvMatchInput", () => {
  it("renders the job description textarea and dropzone prompt", () => {
    render(<CvMatchInput />)
    expect(
      screen.getByPlaceholderText("Wklej tutaj treść ogłoszenia o pracę..."),
    ).toBeInTheDocument()
    expect(screen.getByText("Upuść plik PDF tutaj lub kliknij, aby wybrać")).toBeInTheDocument()
    expect(screen.getByText("Tylko pliki PDF")).toBeInTheDocument()
  })

  it("enables the matching button and shows no progress bar initially", () => {
    render(<CvMatchInput />)
    expect(screen.getByRole("button", { name: "Rozpocznij matchowanie" })).toBeEnabled()
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument()
  })

  it("shows the selected file after a PDF is dropped and allows removing it", async () => {
    render(<CvMatchInput />)

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

  it("starts matching and increments progress up to 90%, disabling the button meanwhile", async () => {
    jest.useFakeTimers()
    render(<CvMatchInput />)

    const button = screen.getByRole("button", { name: "Rozpocznij matchowanie" })
    fireEvent.click(button)

    expect(screen.getByRole("button", { name: "Matchowanie..." })).toBeDisabled()
    expect(screen.getByRole("progressbar")).toBeInTheDocument()

    act(() => {
      jest.advanceTimersByTime(300 * 20)
    })

    const indicator = document.querySelector('[data-slot="progress-indicator"]') as HTMLElement
    expect(indicator.style.transform).toBe("translateX(-10%)")

    jest.useRealTimers()
  })
})
