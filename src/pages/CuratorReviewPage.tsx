import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getArchiviewAssets } from '../data/explorer/archiviewAssets'
import type { ArchiviewAnnotation } from '../data/explorer/archiviewAssets'
import { getBuildingById } from '../data/buildings'
import type { Building, Confidence, MemoryTrace } from '../types/building'
import { ConfidenceBadge } from '../components/ConfidenceBadge'

type CuratorAnnotation = ArchiviewAnnotation & {
  traceId?: string
  image_side?: string
}

type AnnotationsPayload = {
  annotations?: CuratorAnnotation[]
  [key: string]: unknown
}

type DraftRow = {
  traceId: string
  title: string
  period: string
  confidence: Confidence
  userMessage: string
  confirmed: boolean
}

type ConfirmedRow = { ann: CuratorAnnotation; draft: DraftRow }

const CONFIDENCE_OPTIONS: { value: Confidence; label: string }[] = [
  { value: 'confirmed', label: 'Подтверждено' },
  { value: 'probable', label: 'Вероятно' },
  { value: 'needs_verification', label: 'Требует проверки' },
  { value: 'typological_hypothesis', label: 'Типологическая гипотеза' },
]

function traceDraft(trace?: MemoryTrace): Omit<DraftRow, 'traceId' | 'confirmed'> {
  return {
    title: trace?.title ?? '',
    period: trace?.period ?? '',
    confidence: trace?.confidence ?? 'needs_verification',
    userMessage: trace?.userMessage ?? '',
  }
}

function nextTraceId(buildingId: string, index: number): string {
  const card = buildingId.match(/MOSCOW_\d+/)?.[0] ?? buildingId
  return `${card}_T${String(index + 1).padStart(3, '0')}`
}

function buildExportSnippet(rows: ConfirmedRow[]): string {
  return rows
    .map(({ ann, draft }) => {
      return [
        `Подсветка #${ann.id}:`,
        `  annotations.json -> "traceId": "${draft.traceId}"`,
        `  moscow00X.ts -> memoryTraces:`,
        `    id: '${draft.traceId}'`,
        `    title: '${draft.title || ann.label_ru}'`,
        `    period: '${draft.period || 'уточняется'}'`,
        `    confidence: '${draft.confidence}'`,
        `    userMessage: '${draft.userMessage || 'Добавить текст куратора'}'`,
      ].join('\n')
    })
    .join('\n\n')
}

function buildingDataFileName(cardId: string): string {
  const num = cardId.match(/MOSCOW_(\d+)/)?.[1]
  return num ? `moscow${num.padStart(3, '0')}.ts` : 'moscow.ts'
}

function tsString(value: string): string {
  return `'${value.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}'`
}

function downloadTextFile(filename: string, content: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function buildMemoryTraceFromDraft(
  ann: CuratorAnnotation,
  draft: DraftRow,
  existing?: MemoryTrace,
): MemoryTrace & { type: string } {
  return {
    id: draft.traceId,
    type: existing?.type ?? ann.class,
    title: draft.title || ann.label_ru,
    period: draft.period || 'уточняется',
    confidence: draft.confidence,
    userMessage: draft.userMessage || 'Добавить текст куратора',
    ...(existing?.overallConfidence !== undefined
      ? { overallConfidence: existing.overallConfidence }
      : {}),
    ...(existing?.imagePath ? { imagePath: existing.imagePath } : {}),
    ...(existing?.imageCaption ? { imageCaption: existing.imageCaption } : {}),
  }
}

function formatMemoryTrace(trace: MemoryTrace & { type: string }): string {
  const lines = [
    '    {',
    `      id: ${tsString(trace.id)},`,
    `      type: ${tsString(trace.type)},`,
    `      title: ${tsString(trace.title)},`,
    `      period: ${tsString(trace.period)},`,
    `      confidence: ${tsString(trace.confidence)},`,
  ]
  if (trace.overallConfidence !== undefined) {
    lines.push(`      overallConfidence: ${trace.overallConfidence},`)
  }
  lines.push(`      userMessage: ${tsString(trace.userMessage)},`)
  if (trace.imagePath) {
    lines.push(`      imagePath: ${tsString(trace.imagePath)},`)
  }
  if (trace.imageCaption) {
    lines.push(`      imageCaption: ${tsString(trace.imageCaption)},`)
  }
  lines.push('    },')
  return lines.join('\n')
}

function buildMemoryTracesExport(
  confirmedRows: ConfirmedRow[],
  tracesById: Map<string, MemoryTrace>,
): string {
  const entries = confirmedRows.map(({ ann, draft }) => {
    const existing = tracesById.get(draft.traceId) ?? (ann.traceId ? tracesById.get(ann.traceId) : undefined)
    return formatMemoryTrace(buildMemoryTraceFromDraft(ann, draft, existing))
  })

  return [
    '// Вставьте эти записи в блок memoryTraces в src/data/buildings/moscow00X.ts',
    '// Если id уже есть — замените запись; если нет — добавьте в конец массива.',
    '',
    ...entries,
  ].join('\n')
}

function buildUpdatedAnnotationsPayload(
  rawPayload: AnnotationsPayload,
  confirmedById: Map<number, DraftRow>,
): AnnotationsPayload {
  const payload = structuredClone(rawPayload)
  payload.annotations = (payload.annotations ?? []).map((ann) => {
    const draft = confirmedById.get(ann.id)
    if (!draft) return ann
    return { ...ann, traceId: draft.traceId }
  })
  return payload
}

function buildReadme(building: Building, confirmedCount: number): string {
  const buildingFile = buildingDataFileName(building.cardId)
  return [
    `КУРАТОРСКИЙ ЭКСПОРТ — ${building.cardId}`,
    `Здание: ${building.name}`,
    `Подтверждено подсветок: ${confirmedCount}`,
    `Дата: ${new Date().toLocaleString('ru-RU')}`,
    '',
    '1. annotations.json',
    `   Куда: public/explorer/${building.cardId}/annotations.json`,
    '   Действие: заменить файл целиком на GitHub (Edit → вставить → Commit).',
    '',
    '2. memory-traces.ts',
    `   Куда: src/data/buildings/${buildingFile}`,
    '   Действие: в блоке memoryTraces: [ ... ] для каждой записи из файла:',
    '   — если id уже есть, заменить эту запись;',
    '   — если id новый, добавить в конец массива.',
    '',
    '3. Commit → Push → на сайте Ctrl+F5.',
    '',
    'Важно: в скачанные файлы попали только строки с галочкой «Подтверждаю».',
  ].join('\n')
}

function downloadCuratorFiles(
  building: Building,
  rawPayload: AnnotationsPayload,
  confirmedRows: ConfirmedRow[],
  tracesById: Map<string, MemoryTrace>,
): void {
  const confirmedById = new Map(confirmedRows.map(({ ann, draft }) => [ann.id, draft]))
  const annotationsContent = `${JSON.stringify(buildUpdatedAnnotationsPayload(rawPayload, confirmedById), null, 2)}\n`
  const memoryTracesContent = `${buildMemoryTracesExport(confirmedRows, tracesById)}\n`
  const readmeContent = `${buildReadme(building, confirmedRows.length)}\n`

  downloadTextFile('annotations.json', annotationsContent, 'application/json;charset=utf-8')
  window.setTimeout(() => {
    downloadTextFile(
      `memory-traces-${building.cardId}.ts`,
      memoryTracesContent,
      'text/plain;charset=utf-8',
    )
  }, 200)
  window.setTimeout(() => {
    downloadTextFile(
      `README-${building.cardId}.txt`,
      readmeContent,
      'text/plain;charset=utf-8',
    )
  }, 400)
}

export function CuratorReviewPage() {
  const { id } = useParams<{ id: string }>()
  const building = id ? getBuildingById(id) : undefined
  const assets = building ? getArchiviewAssets(building.id) : undefined
  const [annotations, setAnnotations] = useState<CuratorAnnotation[]>([])
  const [rawPayload, setRawPayload] = useState<AnnotationsPayload | null>(null)
  const [drafts, setDrafts] = useState<Record<number, DraftRow>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const tracesById = useMemo(() => {
    return new Map(building?.memoryTraces.map((trace) => [trace.id, trace]) ?? [])
  }, [building])

  useEffect(() => {
    if (!building || !assets) return
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = await fetch(assets.annotationsUrl)
        if (!response.ok) throw new Error(`Не удалось загрузить annotations.json (${response.status})`)
        const payload = (await response.json()) as AnnotationsPayload
        const list = payload.annotations ?? []
        if (cancelled) return
        setRawPayload(payload)
        setAnnotations(list)
        setDrafts(
          Object.fromEntries(
            list.map((ann, index) => {
              const trace = ann.traceId ? tracesById.get(ann.traceId) : undefined
              const fallbackTraceId = ann.traceId || nextTraceId(building.id, building.memoryTraces.length + index)
              return [
                ann.id,
                {
                  traceId: fallbackTraceId,
                  ...traceDraft(trace),
                  title: trace?.title ?? ann.label_ru,
                  confirmed: Boolean(trace),
                },
              ]
            }),
          ),
        )
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Неизвестная ошибка')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [assets, building, tracesById])

  if (!building) {
    return (
      <p className="text-arch-muted">
        Здание не найдено. <Link to="/method" className="font-medium text-arch-green underline">На метод</Link>
      </p>
    )
  }

  const rows = annotations.map((ann) => ({ ann, draft: drafts[ann.id] }))
  const confirmedRows = rows.filter(
    (row): row is ConfirmedRow => Boolean(row.draft?.confirmed),
  )
  const readyCount = confirmedRows.length
  const hasMissingLinks = rows.some((row) => !row.ann.traceId)
  const exportSnippet = buildExportSnippet(confirmedRows)

  return (
    <div className="space-y-6">
      <header className="arch-section border-arch-green/20 bg-gradient-to-br from-arch-green-soft to-arch-surface">
        <Link to="/method" className="text-sm font-medium text-arch-green-light hover:text-arch-green-deep">
          ← Метод
        </Link>
        <p className="arch-kicker mt-3 mb-1">Скрытая кураторская страница</p>
        <h1 className="text-2xl font-semibold tracking-tight text-arch-green-deep">
          Проверка подсветок: {building.name}
        </h1>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-arch-muted">
          Отметьте галочкой проверенные строки и нажмите «Скачать готовые файлы» — получите
          <code className="mx-1 rounded bg-arch-surface-2/80 px-1">annotations.json</code>,
          фрагмент для <code className="mx-1 rounded bg-arch-surface-2/80 px-1">memoryTraces</code>
          и короткую инструкцию. Затем загрузите их в репозиторий на GitHub.
        </p>
      </header>

      <section className="arch-section">
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <p className="arch-kicker mb-1">Здание</p>
            <p className="font-semibold text-arch-green-deep">{building.cardId}</p>
            <p className="text-sm text-arch-muted">{building.address}</p>
          </div>
          <div>
            <p className="arch-kicker mb-1">Подсветки</p>
            <p className="font-semibold text-arch-green-deep">{annotations.length}</p>
            <p className="text-sm text-arch-muted">зон из annotations.json</p>
          </div>
          <div>
            <p className="arch-kicker mb-1">Подтверждено</p>
            <p className="font-semibold text-arch-green-deep">
              {readyCount} / {annotations.length}
            </p>
            <p className="text-sm text-arch-muted">отмечено куратором на этой странице</p>
          </div>
        </div>
        {hasMissingLinks && (
          <p className="mt-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">
            У части подсветок нет <code>traceId</code>. Это не ошибка фасада, но перед публикацией
            нужно решить: привязать их к существующему тексту, создать новый текст или оставить как
            техническую подпись Archiview.
          </p>
        )}
      </section>

      {loading && (
        <p className="arch-section text-sm text-arch-muted">Загружаю annotations.json…</p>
      )}

      {error && (
        <p className="arch-section border-red-200 bg-red-50 text-sm text-red-900">{error}</p>
      )}

      {!loading && !error && (
        <section className="arch-section overflow-hidden">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="arch-kicker mb-1">Таблица сверки</p>
              <h2 className="arch-section-title">Подсветка → текст куратора</h2>
            </div>
            <Link
              to={`/building/${building.id}`}
              className="rounded-full border border-arch-line bg-arch-surface px-4 py-2 text-sm font-medium text-arch-green-deep hover:border-arch-green/40 hover:bg-arch-green-soft"
            >
              Открыть публичную карточку
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-[980px] border-separate border-spacing-0 text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-[0.08em] text-arch-muted">
                  <th className="border-b border-arch-line px-3 py-2">#</th>
                  <th className="border-b border-arch-line px-3 py-2">Archiview</th>
                  <th className="border-b border-arch-line px-3 py-2">Связь</th>
                  <th className="border-b border-arch-line px-3 py-2">Кураторский текст</th>
                  <th className="border-b border-arch-line px-3 py-2">Проверка</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(({ ann, draft }) => {
                  const linkedTrace = ann.traceId ? tracesById.get(ann.traceId) : undefined
                  return (
                    <tr key={ann.id} className="align-top">
                      <td className="border-b border-arch-line px-3 py-4 font-semibold text-arch-green-deep">
                        {ann.id}
                      </td>
                      <td className="border-b border-arch-line px-3 py-4">
                        <p className="font-medium text-arch-ink">{ann.label_ru}</p>
                        <p className="mt-1 text-xs text-arch-muted">
                          class: <code>{ann.class}</code>
                          {ann.image_side ? <> · side: <code>{ann.image_side}</code></> : null}
                        </p>
                        {ann.comment ? (
                          <p className="mt-2 text-xs text-arch-muted">{ann.comment}</p>
                        ) : null}
                      </td>
                      <td className="border-b border-arch-line px-3 py-4">
                        <input
                          value={draft?.traceId ?? ''}
                          onChange={(event) =>
                            setDrafts((current) => ({
                              ...current,
                              [ann.id]: {
                                ...(current[ann.id] ?? {
                                  ...traceDraft(),
                                  confirmed: false,
                                }),
                                traceId: event.target.value,
                              },
                            }))
                          }
                          className="w-56 rounded-lg border border-arch-line bg-arch-surface px-2 py-1 font-mono text-xs"
                        />
                        <p className="mt-2 text-xs text-arch-muted">
                          {linkedTrace ? 'Связано с memoryTraces' : 'Нужна проверка связи'}
                        </p>
                      </td>
                      <td className="border-b border-arch-line px-3 py-4">
                        <label className="block text-xs font-semibold text-arch-green-deep">
                          Заголовок
                          <input
                            value={draft?.title ?? ''}
                            onChange={(event) =>
                              setDrafts((current) => ({
                                ...current,
                                [ann.id]: {
                                  ...(current[ann.id] ?? {
                                    traceId: ann.traceId ?? '',
                                    ...traceDraft(),
                                    confirmed: false,
                                  }),
                                  title: event.target.value,
                                },
                              }))
                            }
                            className="mt-1 block w-full rounded-lg border border-arch-line bg-arch-surface px-2 py-1 text-sm font-normal text-arch-ink"
                          />
                        </label>
                        <div className="mt-2 grid gap-2 sm:grid-cols-[1fr_1fr]">
                          <label className="block text-xs font-semibold text-arch-green-deep">
                            Период
                            <input
                              value={draft?.period ?? ''}
                              onChange={(event) =>
                                setDrafts((current) => ({
                                  ...current,
                                  [ann.id]: {
                                    ...(current[ann.id] ?? {
                                      traceId: ann.traceId ?? '',
                                      ...traceDraft(),
                                      confirmed: false,
                                    }),
                                    period: event.target.value,
                                  },
                                }))
                              }
                              className="mt-1 block w-full rounded-lg border border-arch-line bg-arch-surface px-2 py-1 text-sm font-normal text-arch-ink"
                            />
                          </label>
                          <label className="block text-xs font-semibold text-arch-green-deep">
                            Статус
                            <select
                              value={draft?.confidence ?? 'needs_verification'}
                              onChange={(event) =>
                                setDrafts((current) => ({
                                  ...current,
                                  [ann.id]: {
                                    ...(current[ann.id] ?? {
                                      traceId: ann.traceId ?? '',
                                      ...traceDraft(),
                                      confirmed: false,
                                    }),
                                    confidence: event.target.value as Confidence,
                                  },
                                }))
                              }
                              className="mt-1 block w-full rounded-lg border border-arch-line bg-arch-surface px-2 py-1 text-sm font-normal text-arch-ink"
                            >
                              {CONFIDENCE_OPTIONS.map((item) => (
                                <option key={item.value} value={item.value}>
                                  {item.label}
                                </option>
                              ))}
                            </select>
                          </label>
                        </div>
                        <label className="mt-2 block text-xs font-semibold text-arch-green-deep">
                          Текст
                          <textarea
                            value={draft?.userMessage ?? ''}
                            onChange={(event) =>
                              setDrafts((current) => ({
                                ...current,
                                [ann.id]: {
                                  ...(current[ann.id] ?? {
                                    traceId: ann.traceId ?? '',
                                    ...traceDraft(),
                                    confirmed: false,
                                  }),
                                  userMessage: event.target.value,
                                },
                              }))
                            }
                            rows={4}
                            className="mt-1 block w-full rounded-lg border border-arch-line bg-arch-surface px-2 py-1 text-sm font-normal leading-relaxed text-arch-ink"
                          />
                        </label>
                        {draft?.confidence ? (
                          <div className="mt-2">
                            <ConfidenceBadge level={draft.confidence} />
                          </div>
                        ) : null}
                      </td>
                      <td className="border-b border-arch-line px-3 py-4">
                        <label className="flex items-start gap-2 text-sm text-arch-ink/80">
                          <input
                            type="checkbox"
                            checked={Boolean(draft?.confirmed)}
                            onChange={(event) =>
                              setDrafts((current) => ({
                                ...current,
                                [ann.id]: {
                                  ...(current[ann.id] ?? {
                                    traceId: ann.traceId ?? '',
                                    ...traceDraft(),
                                  }),
                                  confirmed: event.target.checked,
                                },
                              }))
                            }
                            className="mt-1"
                          />
                          Подтверждаю: зона и текст соответствуют друг другу
                        </label>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {!loading && !error && rows.length > 0 && (
        <section className="arch-section">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="arch-kicker mb-1">Экспорт</p>
              <h2 className="arch-section-title">Скачать готовые файлы</h2>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-arch-muted">
                В скачивание попадут только строки с галочкой «Подтверждаю» ({readyCount} из{' '}
                {annotations.length}).
              </p>
            </div>
            <button
              type="button"
              disabled={readyCount === 0 || !rawPayload}
              onClick={() => {
                if (!building || !rawPayload) return
                downloadCuratorFiles(building, rawPayload, confirmedRows, tracesById)
              }}
              className="rounded-full bg-arch-green-deep px-5 py-2.5 text-sm font-semibold text-arch-surface transition hover:bg-arch-green disabled:cursor-not-allowed disabled:opacity-50"
            >
              Скачать готовые файлы
            </button>
          </div>
          {readyCount === 0 ? (
            <p className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">
              Сначала отметьте галочкой хотя бы одну проверенную подсветку.
            </p>
          ) : (
            <ul className="list-inside list-disc space-y-1 text-sm text-arch-muted">
              <li>
                <code>annotations.json</code> — полный файл для{' '}
                <code>public/explorer/{building.cardId}/</code>
              </li>
              <li>
                <code>memory-traces-{building.cardId}.ts</code> — записи для{' '}
                <code>src/data/buildings/{buildingDataFileName(building.cardId)}</code>
              </li>
              <li>
                <code>README-{building.cardId}.txt</code> — куда положить каждый файл
              </li>
            </ul>
          )}
        </section>
      )}

      {!loading && !error && rows.length > 0 && confirmedRows.length > 0 && (
        <section className="arch-section">
          <p className="arch-kicker mb-1">Черновик для переноса</p>
          <h2 className="arch-section-title mb-3">Текстовый чек-лист (только подтверждённые)</h2>
          <p className="mb-3 text-sm leading-relaxed text-arch-muted">
            Если удобнее копировать вручную — ниже те же данные, что попадут в скачанные файлы.
          </p>
          <textarea
            readOnly
            value={exportSnippet}
            rows={12}
            className="w-full rounded-xl border border-arch-line bg-arch-surface-2/40 p-3 font-mono text-xs leading-relaxed text-arch-ink"
          />
        </section>
      )}
    </div>
  )
}
