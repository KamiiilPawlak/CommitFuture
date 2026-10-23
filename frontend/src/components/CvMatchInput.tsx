import { useEffect, useState } from "react"
import { useDropzone } from "react-dropzone"
import { FileText, Upload, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

function CvMatchInput() {
  const [file, setFile] = useState<File | null>(null)
  const [isMatching, setIsMatching] = useState(false)
  const [progress, setProgress] = useState(0)

  const onDrop = (acceptedFiles: File[]) => {
    setFile(acceptedFiles[0] ?? null)
  }

  const removeFile = (event: React.MouseEvent) => {
    event.stopPropagation()
    setFile(null)
  }

  const startMatching = () => {
    setIsMatching(true)
    setProgress(0)
  }

  useEffect(() => {
    if (!isMatching) return

    const interval = setInterval(() => {
      setProgress((previous) => Math.min(previous + 10, 90))
    }, 300)

    return () => clearInterval(interval)
  }, [isMatching])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
  })

  return (
    <div className="mx-auto w-full flex flex-col gap-4">
      <section className="flex flex-col gap-2">
        <textarea
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
          onClick={startMatching}
          disabled={isMatching}
          className="h-10 bg-chart-5 text-accent-foreground hover:bg-chart-5/80!"
        >
          {isMatching ? "Matchowanie..." : "Rozpocznij matchowanie"}
        </Button>
        {isMatching && <Progress value={progress} className="[&>div]:bg-chart-5" />}
      </section>
    </div>
  )
}

export { CvMatchInput }
