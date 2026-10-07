import { useState } from "react"
import { useNavigate } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { useCvStore } from "@/store/cvStore"

function UploadPage() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const upload = useCvStore((state) => state.upload)
  const uploadStatus = useCvStore((state) => state.uploadStatus)
  const uploadError = useCvStore((state) => state.uploadError)

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!file) return

    try {
      const cvDocumentId = await upload(file)
      navigate(`/cv/${cvDocumentId}`)
    } catch {
      // błąd jest już zapisany w store (uploadError)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <form onSubmit={handleSubmit} className="flex w-full max-w-sm flex-col items-center gap-4">
        <h1 className="text-2xl font-semibold text-foreground">CommitFuture</h1>
        <input
          type="file"
          accept="application/pdf"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          className="w-full text-sm text-foreground"
        />
        {uploadStatus === "error" && <p className="text-sm text-destructive">{uploadError}</p>}
        <Button type="submit" disabled={!file || uploadStatus === "uploading"}>
          {uploadStatus === "uploading" ? "Przesyłanie..." : "Prześlij CV"}
        </Button>
      </form>
    </div>
  )
}

export default UploadPage
