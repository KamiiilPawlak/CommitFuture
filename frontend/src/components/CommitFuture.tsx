import logo from "@/assets/logo-cf.png"

function CommitFuture() {
  return (
    <div className="flex shrink-0 items-center gap-2 text-center">
      <img src={logo} alt="CommitFuture" className="h-9 w-auto shrink-0 object-contain sm:h-11" />
      <span className="text-base font-semibold tracking-tight text-foreground sm:text-lg">
        <span className="text-chart-5">Commit</span>Future
      </span>
    </div>
  )
}

export { CommitFuture }
