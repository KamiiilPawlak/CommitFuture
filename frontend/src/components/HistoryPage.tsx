function HistoryPage() {
  return (
    <main className="w-full flex-1 flex flex-col p-5">
      <section className="mx-auto w-full flex flex-col items-center justify-center gap-2 border border-dashed border-border rounded-md p-8 text-center">
        <p className="text-sm font-medium">Historia dopasowań</p>
        <p className="text-xs text-muted-foreground">
          Tu pojawi się lista wcześniejszych wyników matchowania.
        </p>
      </section>
    </main>
  )
}

export { HistoryPage }
