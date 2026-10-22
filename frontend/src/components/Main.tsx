import { CvMatchInput } from "./CvMatchInput"
import { CvMatchOutput } from "./CvMatchOutput"

function Main() {
  return (
    <main className="w-full flex-1 flex flex-col md:flex-row gap-6">
      <CvMatchInput />
      <CvMatchOutput />
    </main>
  )
}

export { Main }
