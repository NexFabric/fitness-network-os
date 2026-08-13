import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, ApiError } from '../api/client'
import { Alert, EmptyState, LoadingSkeleton, PageHeader, StatusBadge } from '../components/ui'

type Template = {
  id: string
  code: string
  name: string
  channel: string
  subject_template: string | null
  body_template: string
  is_active: boolean
  locale: string | null
}

type Delivery = {
  id: string
  channel: string
  status: string
  recipient_address: string | null
  subject: string | null
  error_message: string | null
  attempt_count: number
  created: boolean | null
}

const CHANNELS = ['EMAIL', 'SMS', 'PUSH', 'WHATSAPP'] as const

function formatApiError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    if (e.status === 403) return 'Bu işlem için yetkiniz yok.'
    return e.status === 400 ? e.message : `${e.status}: ${e.message}`
  }
  if (e instanceof Error) return e.message
  return fallback
}

export default function Notifications() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [channel, setChannel] = useState<string>('EMAIL')
  const [subject, setSubject] = useState('')
  const [bodyTemplate, setBodyTemplate] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [createMessage, setCreateMessage] = useState<string | null>(null)

  const [sendChannel, setSendChannel] = useState<string>('EMAIL')
  const [recipient, setRecipient] = useState('')
  const [sendTemplate, setSendTemplate] = useState('')
  const [sendSubject, setSendSubject] = useState('')
  const [sendBody, setSendBody] = useState('')
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)
  const [lastDelivery, setLastDelivery] = useState<Delivery | null>(null)
  const [deliveries, setDeliveries] = useState<Delivery[]>([])

  const load = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) {
      setLoading(true)
      setError(null)
    }
    try {
      const [templateRows, deliveryRows] = await Promise.all([
        api<Template[]>('/api/v1/notifications/templates'),
        api<Delivery[]>('/api/v1/notifications/deliveries?limit=50'),
      ])
      setTemplates(templateRows)
      setDeliveries(deliveryRows)
      setError(null)
    } catch (e) {
      setError(formatApiError(e, 'Şablonlar yüklenemedi'))
    } finally {
      if (!opts?.silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    setCreateError(null)
    setCreateMessage(null)

    if (!code.trim() || !name.trim() || !bodyTemplate.trim()) {
      setCreateError('Kod, isim ve gövde alanları gereklidir.')
      return
    }

    setCreating(true)
    try {
      await api<Template>('/api/v1/notifications/templates', {
        method: 'POST',
        body: {
          code: code.trim(),
          name: name.trim(),
          channel,
          body_template: bodyTemplate,
          subject_template: subject.trim() || null,
        },
      })
      setCode('')
      setName('')
      setSubject('')
      setBodyTemplate('')
      setCreateMessage('Şablon oluşturuldu.')
      await load({ silent: true })
    } catch (err) {
      setCreateError(formatApiError(err, 'Şablon oluşturulamadı'))
    } finally {
      setCreating(false)
    }
  }

  async function handleSend(e: FormEvent) {
    e.preventDefault()
    setSendError(null)
    setLastDelivery(null)

    if (!recipient.trim()) {
      setSendError('Alıcı adresi gereklidir.')
      return
    }
    if (!sendTemplate && !sendBody.trim()) {
      setSendError('Şablon seçin veya bir gövde metni yazın.')
      return
    }

    setSending(true)
    try {
      const result = await api<Delivery>('/api/v1/notifications/deliveries', {
        method: 'POST',
        body: {
          channel: sendChannel,
          recipient_address: recipient.trim(),
          template_code: sendTemplate || null,
          subject: sendSubject.trim() || null,
          body: sendBody.trim() || null,
        },
      })
      setLastDelivery(result)
      await load({ silent: true })
    } catch (err) {
      setSendError(formatApiError(err, 'Gönderim planlanamadı'))
    } finally {
      setSending(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Bildirimler"
        subtitle="Şablonlar ve tek seferlik gönderimler"
      />

      {error && (
        <div className="mt-6">
          <Alert onRetry={() => void load()}>{error}</Alert>
        </div>
      )}

      <section className="card mt-6" aria-labelledby="create-template-heading">
        <div className="card-header">
          <h2 id="create-template-heading" className="text-base font-semibold text-slate-100">
            Şablon oluştur
          </h2>
        </div>
        <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={handleCreate} noValidate>
          <div>
            <label htmlFor="tpl_code" className="label-text">
              Kod <span className="text-teal-500">*</span>
            </label>
            <input
              id="tpl_code"
              type="text"
              required
              maxLength={100}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="input-field"
              disabled={creating}
              placeholder="uyelik_bitis_hatirlatma"
            />
          </div>
          <div>
            <label htmlFor="tpl_name" className="label-text">
              İsim <span className="text-teal-500">*</span>
            </label>
            <input
              id="tpl_name"
              type="text"
              required
              maxLength={255}
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input-field"
              disabled={creating}
            />
          </div>
          <div>
            <label htmlFor="tpl_channel" className="label-text">
              Kanal
            </label>
            <select
              id="tpl_channel"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              className="input-field"
              disabled={creating}
            >
              {CHANNELS.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="tpl_subject" className="label-text">
              Konu şablonu
            </label>
            <input
              id="tpl_subject"
              type="text"
              maxLength={255}
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="input-field"
              disabled={creating}
              placeholder="Üyeliğiniz {{gun}} gün sonra bitiyor"
            />
          </div>
          <div className="sm:col-span-2">
            <label htmlFor="tpl_body" className="label-text">
              Gövde şablonu <span className="text-teal-500">*</span>
            </label>
            <textarea
              id="tpl_body"
              required
              rows={3}
              value={bodyTemplate}
              onChange={(e) => setBodyTemplate(e.target.value)}
              className="input-field"
              disabled={creating}
            />
          </div>
          <div className="flex flex-wrap items-center gap-3 sm:col-span-2">
            <button type="submit" className="btn-primary" disabled={creating}>
              {creating ? 'Oluşturuluyor…' : 'Şablon oluştur'}
            </button>
            {createError && <Alert variant="error">{createError}</Alert>}
            {createMessage && <Alert variant="success">{createMessage}</Alert>}
          </div>
        </form>
      </section>

      <section className="card mt-6" aria-labelledby="template-list-heading">
        <div className="card-header">
          <h2 id="template-list-heading" className="text-base font-semibold text-slate-100">
            Şablonlar
          </h2>
        </div>
        {loading ? (
          <div className="mt-4">
            <LoadingSkeleton rows={3} />
          </div>
        ) : templates.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              title="Henüz şablon yok"
              description="Yukarıdaki formla ilk bildirim şablonunu oluşturun."
            />
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-3 py-2">Kod</th>
                  <th className="px-3 py-2">İsim</th>
                  <th className="px-3 py-2">Kanal</th>
                  <th className="px-3 py-2">Konu</th>
                  <th className="px-3 py-2">Durum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {templates.map((t) => (
                  <tr key={t.id}>
                    <td className="px-3 py-3 font-mono text-xs text-slate-300">{t.code}</td>
                    <td className="px-3 py-3 text-slate-200">{t.name}</td>
                    <td className="px-3 py-3 text-slate-400">{t.channel}</td>
                    <td className="px-3 py-3 text-slate-400">{t.subject_template ?? '—'}</td>
                    <td className="px-3 py-3">
                      <StatusBadge status={t.is_active ? 'Aktif' : 'Pasif'} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="card mt-6" aria-labelledby="send-heading">
        <div className="card-header">
          <h2 id="send-heading" className="text-base font-semibold text-slate-100">
            Gönderim planla
          </h2>
        </div>
        <p className="mt-2 text-sm text-slate-400">
          Gönderim kuyruğa alınır; sonucu aşağıda ve geçmiş listesinde görünür.
        </p>
        <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={handleSend} noValidate>
          <div>
            <label htmlFor="send_channel" className="label-text">
              Kanal
            </label>
            <select
              id="send_channel"
              value={sendChannel}
              onChange={(e) => setSendChannel(e.target.value)}
              className="input-field"
              disabled={sending}
            >
              {CHANNELS.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="send_to" className="label-text">
              Alıcı <span className="text-teal-500">*</span>
            </label>
            <input
              id="send_to"
              type="text"
              required
              maxLength={512}
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              className="input-field"
              disabled={sending}
              placeholder="uye@ornek.com"
            />
          </div>
          <div>
            <label htmlFor="send_template" className="label-text">
              Şablon
            </label>
            <select
              id="send_template"
              value={sendTemplate}
              onChange={(e) => setSendTemplate(e.target.value)}
              className="input-field"
              disabled={sending}
            >
              <option value="">Şablonsuz (serbest metin)</option>
              {templates.map((t) => (
                <option key={t.id} value={t.code}>
                  {t.name} ({t.code})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="send_subject" className="label-text">
              Konu
            </label>
            <input
              id="send_subject"
              type="text"
              maxLength={255}
              value={sendSubject}
              onChange={(e) => setSendSubject(e.target.value)}
              className="input-field"
              disabled={sending}
            />
          </div>
          <div className="sm:col-span-2">
            <label htmlFor="send_body" className="label-text">
              Mesaj
            </label>
            <textarea
              id="send_body"
              rows={3}
              value={sendBody}
              onChange={(e) => setSendBody(e.target.value)}
              className="input-field"
              disabled={sending}
            />
          </div>
          <div className="flex flex-wrap items-center gap-3 sm:col-span-2">
            <button type="submit" className="btn-primary" disabled={sending}>
              {sending ? 'Planlanıyor…' : 'Gönderimi planla'}
            </button>
            {sendError && <Alert variant="error">{sendError}</Alert>}
          </div>
        </form>

        {lastDelivery && (
          <div className="mt-4 rounded-lg border border-slate-700 bg-slate-800/50 p-4">
            <p className="text-sm font-semibold text-slate-200">
              {lastDelivery.created === false
                ? 'Bu gönderim zaten kuyrukta (tekrar oluşturulmadı)'
                : 'Gönderim kuyruğa alındı'}
            </p>
            <dl className="mt-2 grid gap-2 text-xs text-slate-400 sm:grid-cols-2">
              <div>
                <dt className="inline">Durum: </dt>
                <dd className="inline text-slate-200">{lastDelivery.status}</dd>
              </div>
              <div>
                <dt className="inline">Kanal: </dt>
                <dd className="inline text-slate-200">{lastDelivery.channel}</dd>
              </div>
              <div>
                <dt className="inline">Alıcı: </dt>
                <dd className="inline text-slate-200">
                  {lastDelivery.recipient_address ?? '—'}
                </dd>
              </div>
              <div>
                <dt className="inline">Deneme: </dt>
                <dd className="inline text-slate-200">{lastDelivery.attempt_count}</dd>
              </div>
            </dl>
            {lastDelivery.error_message && (
              <p className="mt-2 text-xs text-rose-400">{lastDelivery.error_message}</p>
            )}
          </div>
        )}
      </section>

      <section className="card mt-6" aria-labelledby="delivery-list-heading">
        <div className="card-header">
          <h2 id="delivery-list-heading" className="text-base font-semibold text-slate-100">
            Son gönderimler
          </h2>
        </div>
        {loading ? (
          <div className="mt-4">
            <LoadingSkeleton rows={3} />
          </div>
        ) : deliveries.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              title="Henüz gönderim yok"
              description="Planlanan gönderimler burada listelenir."
            />
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-3 py-2">Alıcı</th>
                  <th className="px-3 py-2">Kanal</th>
                  <th className="px-3 py-2">Konu</th>
                  <th className="px-3 py-2">Durum</th>
                  <th className="px-3 py-2">Deneme</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {deliveries.map((d) => (
                  <tr key={d.id}>
                    <td className="px-3 py-3 text-slate-300">{d.recipient_address ?? '—'}</td>
                    <td className="px-3 py-3 text-slate-400">{d.channel}</td>
                    <td className="px-3 py-3 text-slate-400">{d.subject ?? '—'}</td>
                    <td className="px-3 py-3">
                      <StatusBadge status={d.status} />
                      {d.error_message && (
                        <p className="mt-1 text-xs text-rose-400">{d.error_message}</p>
                      )}
                    </td>
                    <td className="px-3 py-3 text-slate-400">{d.attempt_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
