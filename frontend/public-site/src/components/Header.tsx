"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { BrandMark } from "./BrandMark";

const ADMIN_URL =
  process.env.NEXT_PUBLIC_ADMIN_URL?.replace(/\/$/, "") ||
  "http://localhost:5173";

const nav = [
  { href: "/#features", label: "Özellikler" },
  { href: "/#architecture", label: "Mimari" },
  { href: "/#pricing", label: "Fiyatlandırma" },
];

export function Header() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/80 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Link
            href="/"
            className="rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-background group"
            onClick={() => setOpen(false)}
            aria-label="GymClubNex Ana Sayfa"
          >
            <BrandMark size="sm" />
          </Link>
          <nav
            className="hidden md:flex gap-1 text-sm font-medium"
            aria-label="Ana menü"
          >
            {nav.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="rounded-lg px-3 py-2 text-ink-muted transition-colors hover:bg-white/5 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
              >
                {item.label}
              </a>
            ))}
          </nav>
        </div>

        <div className="hidden sm:flex items-center gap-3">
          <a
            href="/#demo"
            className="text-sm font-medium text-ink-muted transition-colors hover:text-foreground px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand rounded-lg"
          >
            Sistemi incele
          </a>
          <a
            href={`${ADMIN_URL}/login`}
            className="btn-glow rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            Giriş yap
          </a>
        </div>

        <button
          type="button"
          className="md:hidden inline-flex h-11 w-11 items-center justify-center rounded-lg border border-border text-foreground hover:bg-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
          aria-expanded={open}
          aria-controls="mobile-nav"
          aria-label={open ? "Menüyü kapat" : "Menüyü aç"}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" />
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M4 7h16M4 12h16M4 17h16" strokeLinecap="round" />
            </svg>
          )}
        </button>
      </div>

      {open && (
        <div
          id="mobile-nav"
          className="md:hidden border-t border-border bg-surface-raised/95 backdrop-blur-xl"
        >
          <nav className="mx-auto flex max-w-7xl flex-col gap-1 px-5 py-4" aria-label="Mobil menü">
            {nav.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="rounded-lg px-3 py-3 text-base font-medium text-foreground hover:bg-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
                onClick={() => setOpen(false)}
              >
                {item.label}
              </a>
            ))}
            <a
              href="/#demo"
              className="rounded-lg px-3 py-3 text-base font-medium text-ink-muted hover:bg-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
              onClick={() => setOpen(false)}
            >
              Sistemi incele
            </a>
            <a
              href={`${ADMIN_URL}/login`}
              className="mt-2 rounded-lg bg-brand px-4 py-3 text-center text-base font-semibold text-white hover:bg-brand-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
              onClick={() => setOpen(false)}
            >
              Giriş yap
            </a>
          </nav>
        </div>
      )}
    </header>
  );
}
