import { render, screen } from "@testing-library/react"

import { CommitFuture } from "@/components/CommitFuture"

describe("CommitFuture", () => {
  it("renders the CommitFuture logo", () => {
    render(<CommitFuture />)
    expect(screen.getByAltText("CommitFuture")).toBeInTheDocument()
  })

  it("renders the wordmark text", () => {
    render(<CommitFuture />)
    expect(screen.getByText("Commit")).toBeInTheDocument()
    expect(screen.getByText("Future")).toBeInTheDocument()
  })
})
