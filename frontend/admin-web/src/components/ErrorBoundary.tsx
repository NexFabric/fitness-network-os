import { Component, type ErrorInfo, type ReactNode } from 'react'

type Props = { children: ReactNode }
type State = { hasError: boolean; error: Error | null }

/**
 * Root-level error boundary that catches render-time exceptions and shows a
 * recovery screen instead of a blank white page.  Class component because
 * React does not expose getDerivedStateFromError / componentDidCatch as hooks.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Structured log — never console.log in production
    // eslint-disable-next-line no-console
    console.error('[ErrorBoundary]', { error, componentStack: info.componentStack })
  }

  private handleReload = () => {
    window.location.reload()
  }

  render() {
    if (!this.state.hasError) return this.props.children

    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-slate-100 font-sans">
        <div className="w-full max-w-md text-center space-y-4">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-500/10 text-3xl border border-rose-500/20">
            ⚠️
          </div>
          <h1 className="text-xl font-extrabold text-white">
            Beklenmeyen bir hata oluştu
          </h1>
          <p className="text-sm text-slate-400">
            Uygulama beklenmeyen bir sorunla karşılaştı. Sayfayı yenileyerek
            devam edebilirsiniz.
          </p>
          <button
            type="button"
            onClick={this.handleReload}
            className="rounded-xl bg-teal-600 px-6 py-2.5 text-sm font-bold text-white hover:bg-teal-500 transition"
          >
            Sayfayı Yenile
          </button>
        </div>
      </div>
    )
  }
}
