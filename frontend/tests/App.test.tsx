import { render, screen } from "@testing-library/react"
import App from "@/app/App"

describe("App", () => {
  it("renders the CommitFuture heading", () => {
    render(<App />)
    expect(screen.getByRole("heading", { name: "CommitFuture" })).toBeInTheDocument()
  })
})
