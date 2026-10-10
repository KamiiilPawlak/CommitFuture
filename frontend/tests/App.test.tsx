import { render, screen } from "@testing-library/react"
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
})
