import { fireEvent, render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"

import App from "@/app/App"

describe("App", () => {
  it("renders the CommitFuture heading on the upload page", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByRole("heading", { name: "Commit Future" })).toBeInTheDocument()
  })

  it("navigates to the history page when 'Historia' is clicked", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole("link", { name: "Historia" }))

    expect(screen.getByText("Historia dopasowań")).toBeInTheDocument()
  })

  it("renders the history page directly when navigating to /historia", () => {
    render(
      <MemoryRouter initialEntries={["/historia"]}>
        <App />
      </MemoryRouter>,
    )

    expect(screen.getByText("Historia dopasowań")).toBeInTheDocument()
  })
})
