import { Link } from "react-router-dom"
import { CommitFuture } from "@/components/CommitFuture"
import { Button, buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import userIcon from "@/assets/icon/user-icon.svg"

function Header() {
  return (
    <header className="sticky top-0 z-10 flex min-h-16 w-full shrink-0 items-center justify-between gap-2 border-b border-border bg-card px-4 py-3 sm:py-2">
      <CommitFuture />
      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        <Link
          to="/"
          className={cn(
            buttonVariants({ variant: "default", size: "sm" }),
            "h-8 cursor-pointer bg-chart-5 px-2.5 text-sm font-semibold text-accent-foreground transition-colors hover:bg-chart-5/80! focus-visible:border-chart-5 focus-visible:ring-chart-5/50 sm:h-9 sm:px-3 sm:text-base",
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
          <img src={userIcon} alt="User Icon" className="h-4 w-4 sm:h-5 sm:w-5" />
        </Button>
      </div>
    </header>
  )
}

export { Header }
