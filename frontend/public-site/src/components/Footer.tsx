import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border bg-background pt-16 pb-8">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4 lg:grid-cols-5">
          <div className="col-span-2 lg:col-span-2">
            <Link href="/" className="flex items-center gap-2.5 focus-visible:outline-none group mb-4">
              <span className="flex h-8 w-8 items-center justify-center rounded bg-brand/10 border border-brand/20 text-sm font-bold text-brand shadow-sm transition group-hover:bg-brand/20 group-hover:border-brand/40">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                </svg>
              </span>
              <span className="text-lg font-bold tracking-tight text-foreground">GymClubNex</span>
            </Link>
            <p className="text-sm leading-6 text-foreground/60 max-w-xs">
              Yeni nesil spor kulüpleri için tasarlanmış, kesintisiz işletim sistemi. Operasyonu bize bırakın, performansa odaklanın.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold leading-6 text-foreground">Platform</h3>
            <ul role="list" className="mt-6 space-y-4">
              <li><Link href="#features" className="text-sm leading-6 text-foreground/60 hover:text-brand transition-colors">Özellikler</Link></li>
              <li><Link href="#architecture" className="text-sm leading-6 text-foreground/60 hover:text-brand transition-colors">Mimari</Link></li>
              <li><Link href="#security" className="text-sm leading-6 text-foreground/60 hover:text-brand transition-colors">Güvenlik</Link></li>
              <li><Link href="#pricing" className="text-sm leading-6 text-foreground/60 hover:text-brand transition-colors">Fiyatlandırma</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold leading-6 text-foreground">Kaynaklar</h3>
            <ul role="list" className="mt-6 space-y-4">
              <li><Link href="#" className="text-sm leading-6 text-foreground/60 hover:text-brand transition-colors">Dokümantasyon</Link></li>
              <li><Link href="#" className="text-sm leading-6 text-foreground/60 hover:text-brand transition-colors">Sistem Durumu</Link></li>
              <li><Link href="#" className="text-sm leading-6 text-foreground/60 hover:text-brand transition-colors">Geliştirici API</Link></li>
              <li><Link href="#" className="text-sm leading-6 text-foreground/60 hover:text-brand transition-colors">İletişim</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold leading-6 text-foreground">Yasal</h3>
            <ul role="list" className="mt-6 space-y-4">
              <li><Link href="#" className="text-sm leading-6 text-foreground/60 hover:text-brand transition-colors">Gizlilik Politikası</Link></li>
              <li><Link href="#" className="text-sm leading-6 text-foreground/60 hover:text-brand transition-colors">Hizmet Şartları</Link></li>
              <li><Link href="#" className="text-sm leading-6 text-foreground/60 hover:text-brand transition-colors">KVKK Metni</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-16 border-t border-border pt-8 sm:mt-20 lg:mt-24 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs leading-5 text-foreground/50">
            &copy; {new Date().getFullYear()} GymClubNex. Tüm hakları saklıdır.
          </p>
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
            </span>
            <span className="text-xs font-mono text-foreground/50">Tüm sistemler operasyonel</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
