import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"

import { Header } from "@/components/Header"

function renderHeader() {
  render(
    <MemoryRouter>
      <Header />
    </MemoryRouter>,
  )
}

describe("Header", () => {
  it("renders the CommitFuture logo and wordmark", () => {
    renderHeader()
    expect(screen.getByAltText("CommitFuture")).toBeInTheDocument()
    expect(screen.getByText("Commit")).toBeInTheDocument()
    expect(screen.getByText("Future")).toBeInTheDocument()
  })

  it("links 'Nowe CV' to the home route", () => {
    renderHeader()
    expect(screen.getByRole("link", { name: "Nowe CV" })).toHaveAttribute("href", "/")
  })

  it("links 'Historia' to the history route", () => {
    renderHeader()
    expect(screen.getByRole("link", { name: "Historia" })).toHaveAttribute("href", "/historia")
  })

  it("renders an account button that opens no menu", () => {
    renderHeader()
    const accountButton = screen.getByRole("button", { name: "Konto" })
    expect(accountButton).toBeInTheDocument()
    expect(screen.queryByRole("menu")).not.toBeInTheDocument()
  })
})
