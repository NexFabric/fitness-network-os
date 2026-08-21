import { useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'
import { Alert, EmptyState, LoadingSkeleton, PageHeader } from '../components/ui'

type ImportBatch = {
  id: string
  filename: string
  status: 'PREVIEW' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  total_rows: number
  valid_rows: number
  invalid_rows: number
  imported_rows: number
  created_at: string
  completed_at: string | null
}

type ImportRow = {
  id: string
  row_number: number
  status: 'VALID' | 'INVALID' | 'IMPORTED' | 'FAILED'
  raw_data: Record<string, string>
  parsed_data: Record<string, string | null> | null
  error_message: string | null
}

type BatchDetail = ImportBatch & {
  rows: ImportRow[]
}

export default function DataImport() {
  const [batches, setBatches] = useState<ImportBatch[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedBatch, setSelectedBatch] = useState<BatchDetail | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  const [csvContent, setCsvContent] = useState('')
  const [filename, setFilename] = useState('members.csv')
  const [uploading, setUploading] = useState(false)
  const [committing, setCommitting] = useState(false)
  const [banner, setBanner] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  async function loadBatches() {
    try {
      const res = await api<ImportBatch[]>('/api/v1/import/batches')
      setBatches(res)
    } catch {
      // Handled silently
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadBatches()
  }, [])

  async function selectBatch(id: string) {
    setLoadingDetail(true)
    setBanner(null)
    try {
      const detail = await api<BatchDetail>(`/api/v1/import/batch/${id}`)
      setSelectedBatch(detail)
    } catch {
      // Handled silently
    } finally {
      setLoadingDetail(false)
    }
  }

  async function handleUploadPreview(e: React.FormEvent) {
    e.preventDefault()
    if (!csvContent.trim()) return

    setUploading(true)
    setBanner(null)
    try {
      const batch = await api<ImportBatch>('/api/v1/import/upload', {
        method: 'POST',
        body: {
          filename: filename.trim() || 'members.csv',
          csv_content: csvContent.trim(),
        },
      })
      setBanner({
        type: 'success',
        text: `Önizleme hazır: ${batch.total_rows} satır incelendi (${batch.valid_rows} geçerli, ${batch.invalid_rows} hatalı).`,
      })
      setCsvContent('')
      await loadBatches()
      await selectBatch(batch.id)
    } catch (err) {
      if (err instanceof ApiError) {
        setBanner({ type: 'error', text: err.message })
      } else {
        setBanner({ type: 'error', text: 'CSV yüklenemedi. Lütfen formatı kontrol edin.' })
      }
    } finally {
      setUploading(false)
    }
  }

  async function handleCommit(batchId: string) {
    setCommitting(true)
    setBanner(null)
    try {
      const committed = await api<ImportBatch>(`/api/v1/import/batch/${batchId}/commit`, {
        method: 'POST',
      })
      setBanner({
        type: 'success',
        text: `Başarıyla tamamlandı: ${committed.imported_rows} üye sisteme aktarıldı.`,
      })
      await loadBatches()
      await selectBatch(batchId)
    } catch (err) {
      if (err instanceof ApiError) {
        setBanner({ type: 'error', text: err.message })
      } else {
        setBanner({ type: 'error', text: 'İçe aktarma sırasında hata oluştu.' })
      }
    } finally {
      setCommitting(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Veri Göçü & CSV İçe Aktarma"
        subtitle="Eski sisteminizdeki üyeleri CSV formatında toplu olarak doğrulayın, önizleyin ve tek seferde içe aktarın."
      />

      {banner && (
        <div className="mt-4">
          <Alert variant={banner.type === 'success' ? 'success' : 'error'}>
            {banner.text}
          </Alert>
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Upload Form & Past Batches */}
        <div className="lg:col-span-5 space-y-6">
          {/* Upload Card */}
          <div className="card p-5">
            <h2 className="text-sm font-bold uppercase tracking-wide text-ink-muted">
              Yeni CSV Yükle / Yapıştır
            </h2>
            <p className="mt-1 text-xs text-slate-400">
              Gerekli sütunlar: <span className="font-mono text-brand">first_name/ad, last_name/soyad, email, phone, member_number</span>
            </p>

            <form onSubmit={handleUploadPreview} className="mt-4 space-y-3">
              <div>
                <label htmlFor="csv-filename" className="block text-xs font-semibold text-slate-300">
                  Dosya Adı / Açıklama
                </label>
                <input
                  id="csv-filename"
                  type="text"
                  value={filename}
                  onChange={(e) => setFilename(e.target.value)}
                  placeholder="eski_sistem_uyeler.csv"
                  className="input-field mt-1 w-full text-[16px] sm:text-xs"
                />
              </div>

              <div>
                <label htmlFor="csv-content" className="block text-xs font-semibold text-slate-300">
                  CSV İçeriği (veya Dosya Metnini Buraya Yapıştırın)
                </label>
                <textarea
                  id="csv-content"
                  rows={6}
                  value={csvContent}
                  onChange={(e) => setCsvContent(e.target.value)}
                  placeholder={`ad,soyad,eposta,telefon,uye_no\nAhmet,Yilmaz,ahmet@example.com,5551112233,MBR-1001\nAyse,Demir,ayse@example.com,5552223344,MBR-1002`}
                  className="input-field mt-1 w-full font-mono text-[16px] sm:text-xs"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={uploading || !csvContent.trim()}
                className="btn-primary w-full justify-center py-2.5 font-bold"
              >
                {uploading ? 'Doğrulanıyor…' : 'CSV Doğrula ve Önizleme Oluştur'}
              </button>
            </form>
          </div>

          {/* Past Batches List */}
          <div className="card p-5">
            <h2 className="text-sm font-bold uppercase tracking-wide text-ink-muted">
              Önceki İçe Aktarma Grupları
            </h2>
            {loading && <LoadingSkeleton rows={3} />}
            {!loading && batches.length === 0 && (
              <p className="mt-3 text-xs text-slate-500">Henüz içe aktarma grubu bulunmuyor.</p>
            )}
            {!loading && batches.length > 0 && (
              <div className="mt-3 space-y-2 max-h-72 overflow-y-auto">
                {batches.map((b) => (
                  <button
                    key={b.id}
                    type="button"
                    onClick={() => selectBatch(b.id)}
                    className={`w-full text-left rounded-xl border p-3 transition-all ${
                      selectedBatch?.id === b.id
                        ? 'border-brand bg-brand/10 shadow-sm'
                        : 'border-slate-800 bg-slate-900/60 hover:bg-slate-800/60'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-slate-100">{b.filename}</span>
                      <span
                        className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                          b.status === 'COMPLETED'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : b.status === 'PREVIEW'
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {b.status}
                      </span>
                    </div>
                    <div className="mt-1 flex items-center justify-between text-xs text-slate-400">
                      <span>{b.total_rows} Satır ({b.valid_rows} Geçerli)</span>
                      <span>{new Date(b.created_at).toLocaleDateString('tr-TR')}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Batch Preview & Staging Table */}
        <div className="lg:col-span-7">
          {!selectedBatch && (
            <div className="card flex h-full min-h-[420px] items-center justify-center p-8 text-center">
              <EmptyState
                title="Grup Seçilmedi"
                description="Önizlemek ve içe aktarımı onaylamak için soldan bir grup seçin veya yukarıdan yeni bir CSV yükleyin."
              />
            </div>
          )}

          {selectedBatch && loadingDetail && (
            <div className="card p-6">
              <LoadingSkeleton rows={6} />
            </div>
          )}

          {selectedBatch && !loadingDetail && (
            <div className="space-y-4">
              {/* Batch Summary Strip */}
              <div className="card p-5 border-slate-800 bg-slate-900">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-extrabold text-white">{selectedBatch.filename}</h2>
                    <p className="mt-0.5 text-xs text-slate-400">
                      Oluşturulma: {new Date(selectedBatch.created_at).toLocaleString('tr-TR')}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-slate-800 px-2.5 py-1 text-xs font-semibold text-slate-300">
                      Toplam: {selectedBatch.total_rows}
                    </span>
                    <span className="rounded bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 text-xs font-semibold text-emerald-400">
                      Geçerli: {selectedBatch.valid_rows}
                    </span>
                    {selectedBatch.invalid_rows > 0 && (
                      <span className="rounded bg-rose-500/10 border border-rose-500/20 px-2.5 py-1 text-xs font-semibold text-rose-400">
                        Hatalı: {selectedBatch.invalid_rows}
                      </span>
                    )}
                  </div>
                </div>

                {selectedBatch.status === 'PREVIEW' && (
                  <div className="mt-4 border-t border-slate-800 pt-4 flex items-center justify-between">
                    <p className="text-xs text-slate-400">
                      Doğrulanan <strong className="text-emerald-400">{selectedBatch.valid_rows}</strong> geçerli üye aktarılmaya hazır.
                    </p>
                    <button
                      type="button"
                      disabled={committing || selectedBatch.valid_rows === 0}
                      onClick={() => handleCommit(selectedBatch.id)}
                      className="btn-primary py-2 px-4 text-xs font-bold"
                    >
                      {committing ? 'Aktarılıyor…' : 'Geçerli Kayıtları İçe Aktar'}
                    </button>
                  </div>
                )}

                {selectedBatch.status === 'COMPLETED' && (
                  <div className="mt-4 border-t border-slate-800 pt-4">
                    <p className="text-xs font-semibold text-emerald-400">
                      ✓ Bu grup başarıyla tamamlandı ({selectedBatch.imported_rows} üye veritabanına aktarıldı).
                    </p>
                  </div>
                )}
              </div>

              {/* Rows Staging Table */}
              <div className="card p-4 border-slate-800 bg-slate-900/60 overflow-x-auto">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                  Satır Detayları & Doğrulama Raporu
                </h3>
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="pb-2 pl-2">#</th>
                      <th className="pb-2">Durum</th>
                      <th className="pb-2">İsim Soyisim</th>
                      <th className="pb-2">E-posta</th>
                      <th className="pb-2">Telefon</th>
                      <th className="pb-2">Üye No</th>
                      <th className="pb-2 pr-2">Hata / Açıklama</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {selectedBatch.rows.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-800/40">
                        <td className="py-2.5 pl-2 font-mono text-slate-500">{r.row_number}</td>
                        <td className="py-2.5">
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                              r.status === 'VALID' || r.status === 'IMPORTED'
                                ? 'bg-emerald-500/10 text-emerald-400'
                                : 'bg-rose-500/10 text-rose-400'
                            }`}
                          >
                            {r.status}
                          </span>
                        </td>
                        <td className="py-2.5 font-medium text-slate-200">
                          {r.parsed_data?.first_name || r.raw_data.first_name || r.raw_data.ad || '—'}{' '}
                          {r.parsed_data?.last_name || r.raw_data.last_name || r.raw_data.soyad || '—'}
                        </td>
                        <td className="py-2.5 text-slate-400">
                          {r.parsed_data?.email || r.raw_data.email || r.raw_data.eposta || '—'}
                        </td>
                        <td className="py-2.5 text-slate-400">
                          {r.parsed_data?.phone || r.raw_data.phone || r.raw_data.telefon || '—'}
                        </td>
                        <td className="py-2.5 font-mono text-slate-300">
                          {r.parsed_data?.member_number || r.raw_data.member_number || r.raw_data.uye_no || '—'}
                        </td>
                        <td className="py-2.5 pr-2 text-rose-400 max-w-xs truncate" title={r.error_message || ''}>
                          {r.error_message || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
