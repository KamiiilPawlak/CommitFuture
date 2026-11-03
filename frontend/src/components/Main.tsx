import { useState } from "react"
import { CvMatchInput } from "./CvMatchInput"
import { CvMatchOutput } from "./CvMatchOutput"
import type { MatchResultResponse } from "@/lib/api/types"

function Main() {
  const [matchResult, setMatchResult] = useState<MatchResultResponse | null>(null)

  return (
    <main className="w-full flex-1 flex flex-col md:flex-row gap-6 p-5">
      <CvMatchInput onMatchResult={setMatchResult} />
      <CvMatchOutput result={matchResult} />
    </main>
  )
}

export { Main }
