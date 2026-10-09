import { Link } from "react-router-dom"

import logo from "@/assets/logo-cf.png"
import { Button, buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"

function Header() {
  return (
    <header className="sticky top-0 z-10 flex min-h-16 w-full shrink-0 items-center justify-between gap-2 border-b border-border bg-card px-4 py-3 sm:py-2">
      <div className="flex shrink-0 items-center gap-2 text-center">
        <img src={logo} alt="CommitFuture" className="h-9 w-auto shrink-0 object-contain sm:h-11" />
        <span className="text-base font-semibold tracking-tight text-foreground sm:text-lg">
          <span className="text-chart-5">Commit</span>Future
        </span>
      </div>
      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        <Link
          to="/"
          className={cn(
            buttonVariants({ variant: "default", size: "sm" }),
            "h-8 cursor-pointer bg-chart-5 px-2.5 text-sm font-semibold text-black transition-colors hover:bg-chart-5/80! focus-visible:border-chart-5 focus-visible:ring-chart-5/50 sm:h-9 sm:px-3 sm:text-base",
          )}
        >
          Nowe CV
        </Link>
        <nav className="hidden items-center gap-1 sm:flex sm:gap-2">
          <Link
            to="/historia"
            className={cn(
              buttonVariants({ variant: "ghost", size: "sm" }),
              "h-8 cursor-pointer px-2 text-sm font-semibold text-foreground transition-colors hover:bg-muted sm:h-9 sm:px-2.5 sm:text-base",
            )}
          >
            Historia
          </Link>
        </nav>
        <div className="hidden h-5 w-px shrink-0 bg-border sm:block" aria-hidden="true" />
        <Button
          variant="ghost"
          size="icon"
          aria-label="Konto"
          className="size-8 shrink-0 cursor-pointer rounded-full text-foreground transition-colors hover:bg-muted sm:size-9"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="size-4.5"
          >
            <circle cx="12" cy="8" r="4" />
            <path d="M4 20c0-3.5 3.5-6 8-6s8 2.5 8 6" />
          </svg>
        </Button>
      </div>
    </header>
  )
}

export { Header }
