import Link from "next/link";

export function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2.5 focus-visible:outline-none group">
            <span
              className="flex h-8 w-8 items-center justify-center rounded bg-brand/10 border border-brand/20 text-sm font-bold text-brand shadow-sm transition group-hover:bg-brand/20 group-hover:border-brand/40"
              aria-hidden="true"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </span>
            <span className="text-lg font-bold tracking-tight text-foreground">
              GymClubNex
            </span>
          </Link>
          <nav className="hidden md:flex gap-6 text-sm font-medium text-foreground/70">
            <Link href="#features" className="hover:text-foreground transition-colors">Özellikler</Link>
            <Link href="#architecture" className="hover:text-foreground transition-colors">Mimari</Link>
            <Link href="#pricing" className="hover:text-foreground transition-colors">Fiyatlandırma</Link>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/#demo" className="text-sm font-medium text-foreground/70 hover:text-foreground transition-colors hidden sm:block">
            Sistemi İncele
          </Link>
          <Link href="http://localhost:5173/login" className="rounded bg-brand px-4 py-2 text-sm font-medium text-white shadow-[0_0_15px_rgba(13,148,136,0.3)] hover:shadow-[0_0_20px_rgba(13,148,136,0.5)] hover:bg-brand-deep transition-all duration-300">
            Giriş Yap
          </Link>
        </div>
      </div>
    </header>
  );
}
