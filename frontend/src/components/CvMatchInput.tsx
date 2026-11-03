import { useEffect, useRef, useState } from "react"
import { useDropzone } from "react-dropzone"
import { FileText, Upload, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { useCvStore } from "@/store/cvStore"
import { ApiError, matchCv } from "@/lib/api/client"
import type { MatchResultResponse } from "@/lib/api/types"

interface CvMatchInputProps {
  onMatchResult: (result: MatchResultResponse | null) => void
}

function CvMatchInput({ onMatchResult }: CvMatchInputProps) {
  const [file, setFile] = useState<File | null>(null)
  const [jobDescription, setJobDescription] = useState("")
  const [cvDocumentId, setCvDocumentId] = useState<string | null>(null)
  const [matchError, setMatchError] = useState<string | null>(null)
  const [isMatchDone, setIsMatchDone] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const matchedDocumentIdRef = useRef<string | null>(null)

  const upload = useCvStore((state) => state.upload)
  const fetchResult = useCvStore((state) => state.fetchResult)
  const cvResult = useCvStore((state) => (cvDocumentId ? state.results[cvDocumentId] : undefined))

  const cvFailed = cvResult?.status === "error"
  const displayedError = matchError ?? (cvFailed ? cvResult.error : null)
  const isMatching = isUploading || (cvDocumentId !== null && !displayedError && !isMatchDone)

  const onDrop = (acceptedFiles: File[]) => {
    setFile(acceptedFiles[0] ?? null)
  }

  const removeFile = (event: React.MouseEvent) => {
    event.stopPropagation()
    setFile(null)
  }

  const startMatching = async () => {
    if (!file || !jobDescription.trim() || isMatching) return

    setMatchError(null)
    setIsMatchDone(false)
    onMatchResult(null)
    matchedDocumentIdRef.current = null
    setIsUploading(true)

    try {
      const newCvDocumentId = await upload(file)
      setCvDocumentId(newCvDocumentId)
      void fetchResult(newCvDocumentId)
    } catch (err) {
      setMatchError(err instanceof ApiError ? err.message : "Nie udało się przesłać CV.")
    } finally {
      setIsUploading(false)
    }
  }

  useEffect(() => {
    if (!cvDocumentId || cvResult?.status !== "success") return
    if (matchedDocumentIdRef.current === cvDocumentId) return
    matchedDocumentIdRef.current = cvDocumentId

    matchCv({ cv_document_id: cvDocumentId, job_posting_raw_text: jobDescription })
      .then((result) => {
        onMatchResult(result)
        setIsMatchDone(true)
      })
      .catch((err: unknown) => {
        setMatchError(err instanceof ApiError ? err.message : "Nie udało się wykonać matchowania.")
      })
  }, [cvDocumentId, cvResult, jobDescription, onMatchResult])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
  })

  const canStartMatching = Boolean(file) && jobDescription.trim().length > 0 && !isMatching

  return (
    <div className="mx-auto w-full flex flex-col gap-4">
      <section className="flex flex-col gap-2">
        <textarea
          value={jobDescription}
          onChange={(event) => setJobDescription(event.target.value)}
          placeholder="Wklej tutaj treść ogłoszenia o pracę..."
          className="min-h-40 resize-none rounded-lg border-2 border-dashed border-border bg-transparent p-4 text-sm outline-none transition-colors placeholder:text-muted-foreground hover:bg-muted/50 focus:border-chart-5 focus:bg-transparent"
        ></textarea>
      </section>
      <section
        {...getRootProps()}
        className={`flex flex-col items-center justify-center gap-2 border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive ? "border-primary bg-muted" : "border-border hover:bg-muted/50"
        }`}
      >
        <input {...getInputProps()} />
        {file ? (
          <>
            <FileText className="size-8 text-primary" />
            <p className="text-sm font-medium">{file.name}</p>
            <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(0)} KB</p>
            <button
              type="button"
              onClick={removeFile}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
            >
              <X className="size-3" />
              Usuń plik
            </button>
          </>
        ) : (
          <>
            <Upload className="size-8 text-muted-foreground" />
            <p className="text-sm font-medium">Upuść plik PDF tutaj lub kliknij, aby wybrać</p>
            <p className="text-xs text-muted-foreground">Tylko pliki PDF</p>
          </>
        )}
      </section>
      <section className="flex flex-col gap-2">
        <Button
          type="button"
          onClick={() => void startMatching()}
          disabled={!canStartMatching}
          className="h-10 bg-chart-5 text-accent-foreground hover:bg-chart-5/80!"
        >
          {isMatching ? "Matchowanie..." : "Rozpocznij matchowanie"}
        </Button>
        {isMatching && (
          <Progress
            value={cvResult?.status === "success" ? 90 : 50}
            className="[&>div]:bg-chart-5"
          />
        )}
        {displayedError && <p className="text-sm text-destructive">{displayedError}</p>}
      </section>
    </div>
  )
}

export { CvMatchInput }
