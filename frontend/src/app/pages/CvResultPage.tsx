import { useEffect } from "react"
import { useParams } from "react-router-dom"

import { useCvStore } from "@/store/cvStore"

function CvResultPage() {
  const { cvDocumentId } = useParams<{ cvDocumentId: string }>()
  const fetchResult = useCvStore((state) => state.fetchResult)
  const entry = useCvStore((state) => (cvDocumentId ? state.results[cvDocumentId] : undefined))

  useEffect(() => {
    if (cvDocumentId) void fetchResult(cvDocumentId)
  }, [cvDocumentId, fetchResult])

  return (
    <div className="flex min-h-screen flex-col items-center gap-4 bg-background p-8 text-foreground">
      <h1 className="text-2xl font-semibold">Wynik analizy CV</h1>
      <p className="text-sm text-muted-foreground">ID dokumentu: {cvDocumentId}</p>
      {(!entry || entry.status === "loading") && (
        <p className="text-sm text-muted-foreground">Ładowanie...</p>
      )}
      {entry?.status === "error" && <p className="text-sm text-destructive">{entry.error}</p>}
      {entry?.status === "success" && (
        <pre className="w-full max-w-2xl overflow-auto rounded-md bg-muted p-4 text-xs">
          {JSON.stringify(entry.data, null, 2)}
        </pre>
      )}
    </div>
  )
}

export default CvResultPage
