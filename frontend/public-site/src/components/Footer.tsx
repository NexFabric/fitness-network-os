import Link from "next/link";
import { BrandMark } from "./BrandMark";

export function Footer() {
  return (
    <footer className="border-t border-border bg-background pt-14 pb-8">
      <div className="mx-auto max-w-7xl px-5 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-10 md:grid-cols-4 lg:grid-cols-5">
          <div className="col-span-2">
            <Link
              href="/"
              className="inline-block rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
              aria-label="GymClubNex Ana Sayfa"
            >
              <BrandMark size="sm" />
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-ink-muted">
              Yeni nesil spor kulüpleri ve federasyonlar için tasarlanmış, kesintisiz işletim
              sistemi. Operasyonu otomatikleştirin, performansa odaklanın.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Platform</h3>
            <ul className="mt-4 space-y-3">
              <li>
                <Link
                  href="/#features"
                  className="text-sm text-ink-muted transition-colors hover:text-brand"
                >
                  Özellikler
                </Link>
              </li>
              <li>
                <Link
                  href="/#architecture"
                  className="text-sm text-ink-muted transition-colors hover:text-brand"
                >
                  Mimari
                </Link>
              </li>
              <li>
                <Link
                  href="/#pricing"
                  className="text-sm text-ink-muted transition-colors hover:text-brand"
                >
                  Fiyatlandırma
                </Link>
              </li>
              <li>
                <Link
                  href="/#demo"
                  className="text-sm text-ink-muted transition-colors hover:text-brand"
                >
                  Demo
                </Link>
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
            <span className="h-2 w-2 rounded-full bg-accent" />
            <span className="font-mono text-xs text-ink-muted">
              Platform Altyapısı · Aktif
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
