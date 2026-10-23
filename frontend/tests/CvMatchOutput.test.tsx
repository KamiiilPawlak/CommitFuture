import { render, screen } from "@testing-library/react"

import { CvMatchOutput } from "@/components/CvMatchOutput"
import { seedMatchResultHigh, seedMatchResultLow } from "./fixtures/matchResult"

describe("CvMatchOutput", () => {
  it("shows the empty-state placeholder when there is no result", () => {
    render(<CvMatchOutput />)
    expect(screen.getByText("Wyniki analizy pojawią się tutaj")).toBeInTheDocument()
  })

  it("renders scores and skill lists for a high-match result", () => {
    render(<CvMatchOutput result={seedMatchResultHigh} />)

    expect(screen.getByText("82%")).toBeInTheDocument()
    expect(screen.getByText("78%")).toBeInTheDocument()
    expect(screen.getAllByText("zgodna", { exact: true })).toHaveLength(2)
    expect(screen.getByText("TypeScript")).toBeInTheDocument()
    expect(screen.getByText("Kubernetes")).toBeInTheDocument()
    expect(screen.getByText("Fintech")).toBeInTheDocument()
  })

  it("shows empty-list fallbacks for a low-match result with no overlap", () => {
    render(<CvMatchOutput result={seedMatchResultLow} />)

    expect(screen.getByText("34%")).toBeInTheDocument()
    expect(screen.getByText("Brak zgodności domenowej")).toBeInTheDocument()
    expect(screen.getByText("Brak wspólnych umiejętności miękkich")).toBeInTheDocument()
  })
})
