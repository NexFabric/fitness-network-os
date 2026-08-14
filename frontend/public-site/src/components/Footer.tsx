import Link from "next/link";
import { BrandMark } from "./BrandMark";

export function Footer() {
  return (
    <footer className="border-t border-border bg-background pt-14 pb-8">
      <div className="mx-auto max-w-7xl px-5 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-10 md:grid-cols-4 lg:grid-cols-5">
          <div className="col-span-2">
            <Link href="/" className="inline-block focus-visible:outline-none">
              <BrandMark size="sm" />
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-ink-muted">
              Yeni nesil spor kulüpleri için tasarlanmış, kesintisiz işletim
              sistemi. Operasyonu bize bırakın, performansa odaklanın.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Platform</h3>
            <ul className="mt-4 space-y-3">
              <li>
                <a
                  href="#features"
                  className="text-sm text-ink-muted transition-colors hover:text-brand"
                >
                  Özellikler
                </a>
              </li>
              <li>
                <a
                  href="#architecture"
                  className="text-sm text-ink-muted transition-colors hover:text-brand"
                >
                  Mimari
                </a>
              </li>
              <li>
                <a
                  href="#pricing"
                  className="text-sm text-ink-muted transition-colors hover:text-brand"
                >
                  Fiyatlandırma
                </a>
              </li>
              <li>
                <a
                  href="#demo"
                  className="text-sm text-ink-muted transition-colors hover:text-brand"
                >
                  Demo
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">İletişim</h3>
            <ul className="mt-4 space-y-3">
              <li>
                <a
                  href="mailto:hello@gymclubnex.com"
                  className="text-sm text-ink-muted transition-colors hover:text-brand"
                >
                  hello@gymclubnex.com
                </a>
              </li>
              <li>
                <a
                  href="mailto:hello@gymclubnex.com?subject=GymClubNex%20Demo"
                  className="text-sm text-ink-muted transition-colors hover:text-brand"
                >
                  Demo talep et
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Yasal</h3>
            <ul className="mt-4 space-y-3">
              <li>
                <Link
                  href="/privacy"
                  className="text-sm text-ink-muted transition-colors hover:text-brand"
                >
                  Gizlilik politikası
                </Link>
              </li>
              <li>
                <Link
                  href="/terms"
                  className="text-sm text-ink-muted transition-colors hover:text-brand"
                >
                  Hizmet şartları
                </Link>
              </li>
              <li>
                <Link
                  href="/kvkk"
                  className="text-sm text-ink-muted transition-colors hover:text-brand"
                >
                  KVKK metni
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 sm:flex-row">
          <p className="text-xs text-ink-muted">
            &copy; {new Date().getFullYear()} GymClubNex. Tüm hakları saklıdır.
          </p>
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
            </span>
            <span className="font-mono text-xs text-ink-muted">
              Platform Altyapısı · Aktif
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
