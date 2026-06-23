import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getArchiviewAssets } from '../data/explorer/archiviewAssets'
import type { ArchiviewAnnotation } from '../data/explorer/archiviewAssets'
import { fetchExpertAnnotationSources } from '../data/explorer/explorerManifest'
import { getBuildingById } from '../data/buildings'
import type { Building, Confidence, MemoryTrace } from '../types/building'
import { ConfidenceBadge } from '../components/ConfidenceBadge'
import { CONFIDENCE_SELECT_OPTIONS } from '../data/confidenceGuide'

type ExpertAnnotation = ArchiviewAnnotation & {
  traceId?: string
  image_side?: string
}

type AnnotationsPayload = {
  annotations?: ExpertAnnotation[]
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

type AnnotationBundle = {
  comparisonId: string
  comparisonTitle: string
  annotationsRelPath: string
  payload: AnnotationsPayload
}

type ExpertTableRow = {
  rowKey: string
  comparisonId: string
  comparisonTitle: string
  annotationsRelPath: string
  ann: ExpertAnnotation
  isNew: boolean
}

type ConfirmedTableRow = ExpertTableRow & { draft: DraftRow }

function traceDraft(trace?: MemoryTrace): Omit<DraftRow, 'traceId' | 'confirmed'> {
  return {
    title: trace?.title ?? '',
    period: trace?.period ?? '',
    confidence: trace?.confidence ?? 'needs_verification',
    userMessage: trace?.userMessage ?? '',
  }
}

/** Предлагаемый traceId для новой подсветки: номер области → T012 для #12. */
function defaultTraceIdForAnnotation(annotationId: number): string {
  return `T${String(annotationId).padStart(3, '0')}`
}

function buildInitialDraft(
  ann: ExpertAnnotation,
  tracesById: Map<string, MemoryTrace>,
): DraftRow {
  const traceId = ann.traceId || defaultTraceIdForAnnotation(ann.id)
  const trace =
    (ann.traceId ? tracesById.get(ann.traceId) : undefined) ?? tracesById.get(traceId)
  return {
    traceId,
    ...traceDraft(trace),
    title: trace?.title ?? ann.label_ru,
    confirmed: Boolean(trace && ann.traceId),
  }
}

function buildExportSnippet(rows: ConfirmedTableRow[]): string {
  return rows
    .map(({ ann, draft, comparisonTitle }) => {
      return [
        `Подсветка #${ann.id}${comparisonTitle ? ` (${comparisonTitle})` : ''}:`,
        `  annotations.json -> "traceId": "${draft.traceId}"`,
        `  moscow00X.ts -> memoryTraces:`,
        `    id: '${draft.traceId}'`,
        `    title: '${draft.title || ann.label_ru}'`,
        `    period: '${draft.period || 'уточняется'}'`,
        `    confidence: '${draft.confidence}'`,
        `    userMessage: '${draft.userMessage || 'Добавить текст эксперта'}'`,
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
  ann: ExpertAnnotation,
  draft: DraftRow,
  existing?: MemoryTrace,
): MemoryTrace & { type: string } {
  return {
    id: draft.traceId,
    type: existing?.type ?? ann.class,
    title: draft.title || ann.label_ru,
    period: draft.period || 'уточняется',
    confidence: draft.confidence,
    userMessage: draft.userMessage || 'Добавить текст эксперта',
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
  confirmedRows: ConfirmedTableRow[],
  tracesById: Map<string, MemoryTrace>,
): string {
  const entries = confirmedRows.map(({ ann, draft }) => {
    const existing =
      tracesById.get(draft.traceId) ?? (ann.traceId ? tracesById.get(ann.traceId) : undefined)
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
  confirmedByAnnId: Map<number, DraftRow>,
): AnnotationsPayload {
  const payload = structuredClone(rawPayload)
  payload.annotations = (payload.annotations ?? []).map((ann) => {
    const draft = confirmedByAnnId.get(ann.id)
    if (!draft) return ann
    return { ...ann, traceId: draft.traceId }
  })
  return payload
}

function buildReadme(
  building: Building,
  confirmedCount: number,
  annotationPaths: string[],
): string {
  const buildingFile = buildingDataFileName(building.cardId)
  const annLines = annotationPaths.map(
    (rel) => `   — public/explorer/${building.cardId}/${rel}`,
  )
  return [
    `КУРАТОРСКИЙ ЭКСПОРТ — ${building.cardId}`,
    `Здание: ${building.name}`,
    `Подтверждено подсветок: ${confirmedCount}`,
    `Дата: ${new Date().toLocaleString('ru-RU')}`,
    '',
    '1. annotations.json (по одному файлу на сравнение, если их несколько)',
    ...annLines,
    '   Действие: заменить соответствующий файл на GitHub.',
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
    '',
    'Новые подсветки из Archiview появятся здесь после «Отправить на сайт» → Push → «Обновить список».',
  ].join('\n')
}

function downloadExpertFiles(
  building: Building,
  bundles: AnnotationBundle[],
  confirmedRows: ConfirmedTableRow[],
  tracesById: Map<string, MemoryTrace>,
): void {
  const paths: string[] = []
  bundles.forEach((bundle) => {
    const confirmedInBundle = confirmedRows.filter(
      (row) => row.annotationsRelPath === bundle.annotationsRelPath,
    )
    if (confirmedInBundle.length === 0) return
    const confirmedByAnnId = new Map(
      confirmedInBundle.map(({ ann, draft }) => [ann.id, draft]),
    )
    const annotationsContent = `${JSON.stringify(
      buildUpdatedAnnotationsPayload(bundle.payload, confirmedByAnnId),
      null,
      2,
    )}\n`
    const filename =
      bundle.annotationsRelPath === 'annotations.json'
        ? 'annotations.json'
        : bundle.annotationsRelPath.replace(/\//g, '-')
    paths.push(bundle.annotationsRelPath)
    downloadTextFile(filename, annotationsContent, 'application/json;charset=utf-8')
  })

  const memoryTracesContent = `${buildMemoryTracesExport(confirmedRows, tracesById)}\n`
  const readmeContent = `${buildReadme(building, confirmedRows.length, paths)}\n`

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

function flattenBundles(
  bundles: AnnotationBundle[],
  tracesById: Map<string, MemoryTrace>,
): { rows: ExpertTableRow[]; drafts: Record<string, DraftRow> } {
  const rows: ExpertTableRow[] = []
  const drafts: Record<string, DraftRow> = {}

  bundles.forEach((bundle) => {
    const list = bundle.payload.annotations ?? []
    list.forEach((ann) => {
      const rowKey = `${bundle.comparisonId}:${ann.id}`
      const isNew = !ann.traceId && !tracesById.has(defaultTraceIdForAnnotation(ann.id))
      rows.push({
        rowKey,
        comparisonId: bundle.comparisonId,
        comparisonTitle: bundle.comparisonTitle,
        annotationsRelPath: bundle.annotationsRelPath,
        ann,
        isNew,
      })
      drafts[rowKey] = buildInitialDraft(ann, tracesById)
    })
  })

  rows.sort((a, b) => {
    if (a.comparisonId !== b.comparisonId) {
      return a.comparisonTitle.localeCompare(b.comparisonTitle, 'ru')
    }
    return a.ann.id - b.ann.id
  })

  return { rows, drafts }
}

export function ExpertReviewPage() {
  const { id } = useParams<{ id: string }>()
  const building = id ? getBuildingById(id) : undefined
  const assets = building ? getArchiviewAssets(building.id) : undefined
  const [bundles, setBundles] = useState<AnnotationBundle[]>([])
  const [tableRows, setTableRows] = useState<ExpertTableRow[]>([])
  const [drafts, setDrafts] = useState<Record<string, DraftRow>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  const tracesById = useMemo(() => {
    return new Map(building?.memoryTraces.map((trace) => [trace.id, trace]) ?? [])
  }, [building])

  const showComparisonColumn = bundles.length > 1

  const loadAnnotations = useCallback(async () => {
    if (!building || !assets) return
    setLoading(true)
    setError(null)
    try {
      const sources = await fetchExpertAnnotationSources(building.cardId, assets.annotationsUrl)
      const loaded: AnnotationBundle[] = []
      for (const source of sources) {
        const response = await fetch(source.annotationsUrl, { cache: 'no-cache' })
        if (!response.ok) {
          throw new Error(
            `Не удалось загрузить ${source.annotationsRelPath} (${response.status})`,
          )
        }
        const payload = (await response.json()) as AnnotationsPayload
        loaded.push({
          comparisonId: source.comparisonId,
          comparisonTitle: source.comparisonTitle,
          annotationsRelPath: source.annotationsRelPath,
          payload,
        })
      }
      const { rows, drafts: nextDrafts } = flattenBundles(loaded, tracesById)
      setBundles(loaded)
      setTableRows(rows)
      setDrafts(nextDrafts)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка')
    } finally {
      setLoading(false)
    }
  }, [assets, building, tracesById])

  useEffect(() => {
    void loadAnnotations()
  }, [loadAnnotations, reloadToken])

  const patchDraft = useCallback((rowKey: string, patch: Partial<DraftRow>, row: ExpertTableRow) => {
    setDrafts((current) => ({
      ...current,
      [rowKey]: {
        ...(current[rowKey] ?? buildInitialDraft(row.ann, tracesById)),
        ...patch,
      },
    }))
  }, [tracesById])

  if (!building) {
    return (
      <p className="text-arch-muted">
        Здание не найдено. <Link to="/method" className="font-medium text-arch-green underline">На метод</Link>
      </p>
    )
  }

  const rows = tableRows.map((row) => ({ ...row, draft: drafts[row.rowKey] }))
  const confirmedRows = rows.filter((row): row is ConfirmedTableRow => Boolean(row.draft?.confirmed))
  const readyCount = confirmedRows.length
  const newCount = rows.filter((row) => row.isNew).length
  const hasMissingLinks = rows.some((row) => !row.ann.traceId)
  const exportSnippet = buildExportSnippet(confirmedRows)

  return (
    <div className="space-y-6">
      <header className="arch-section border-arch-green/20 bg-gradient-to-br from-arch-green-soft to-arch-surface">
        <Link to="/method" className="text-sm font-medium text-arch-green-light hover:text-arch-green-deep">
          ← Метод
        </Link>
        <p className="arch-kicker mt-3 mb-1">Скрытая экспертная страница</p>
        <h1 className="text-2xl font-semibold tracking-tight text-arch-green-deep">
          Проверка подсветок: {building.name}
        </h1>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-arch-muted">
          Список подсветок подгружается из <code className="rounded bg-arch-surface-2/80 px-1">manifest.json</code>{' '}
          (все сравнения Archiview на сайте). Добавили зону в Archiview → «Отправить на сайт» → Push →
          нажмите <strong>Обновить список</strong> здесь.
        </p>
      </header>

      <section className="arch-section">
        <div className="grid gap-4 md:grid-cols-4">
          <div>
            <p className="arch-kicker mb-1">Здание</p>
            <p className="font-semibold text-arch-green-deep">{building.cardId}</p>
            <p className="text-sm text-arch-muted">{building.address}</p>
          </div>
          <div>
            <p className="arch-kicker mb-1">Подсветки</p>
            <p className="font-semibold text-arch-green-deep">{tableRows.length}</p>
            <p className="text-sm text-arch-muted">
              {bundles.length > 1
                ? `из ${bundles.length} сравнений`
                : 'зон из annotations.json'}
            </p>
          </div>
          <div>
            <p className="arch-kicker mb-1">Новые</p>
            <p className="font-semibold text-arch-green-deep">{newCount}</p>
            <p className="text-sm text-arch-muted">без traceId на сайте</p>
          </div>
          <div>
            <p className="arch-kicker mb-1">Подтверждено</p>
            <p className="font-semibold text-arch-green-deep">
              {readyCount} / {tableRows.length}
            </p>
            <p className="text-sm text-arch-muted">отмечено экспертом</p>
          </div>
        </div>
        {hasMissingLinks && (
          <p className="mt-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">
            У части подсветок нет <code>traceId</code> в annotations.json — для новых зон предложен
            черновик (<code>T012</code> для #12). Отредактируйте текст, поставьте галочку и скачайте файлы.
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
              <h2 className="arch-section-title">Подсветка → текст эксперта</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setReloadToken((value) => value + 1)}
                className="rounded-full border border-arch-line bg-arch-surface px-4 py-2 text-sm font-medium text-arch-green-deep hover:border-arch-green/40 hover:bg-arch-green-soft"
              >
                Обновить список
              </button>
              <Link
                to={`/building/${building.id}`}
                className="rounded-full border border-arch-line bg-arch-surface px-4 py-2 text-sm font-medium text-arch-green-deep hover:border-arch-green/40 hover:bg-arch-green-soft"
              >
                Открыть публичную карточку
              </Link>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-[980px] border-separate border-spacing-0 text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-[0.08em] text-arch-muted">
                  <th className="border-b border-arch-line px-3 py-2">#</th>
                  {showComparisonColumn ? (
                    <th className="border-b border-arch-line px-3 py-2">Сравнение</th>
                  ) : null}
                  <th className="border-b border-arch-line px-3 py-2">Archiview</th>
                  <th className="border-b border-arch-line px-3 py-2">Связь</th>
                  <th className="border-b border-arch-line px-3 py-2">Экспертный текст</th>
                  <th className="border-b border-arch-line px-3 py-2">Проверка</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const { ann, draft, rowKey } = row
                  const linkedTrace =
                    (ann.traceId ? tracesById.get(ann.traceId) : undefined) ??
                    (draft?.traceId ? tracesById.get(draft.traceId) : undefined)
                  return (
                    <tr key={rowKey} className="align-top">
                      <td className="border-b border-arch-line px-3 py-4 font-semibold text-arch-green-deep">
                        {ann.id}
                        {row.isNew ? (
                          <span className="mt-1 block text-[10px] font-medium uppercase tracking-wide text-amber-700">
                            новая
                          </span>
                        ) : null}
                      </td>
                      {showComparisonColumn ? (
                        <td className="border-b border-arch-line px-3 py-4 text-xs text-arch-muted">
                          {row.comparisonTitle}
                        </td>
                      ) : null}
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
                            patchDraft(rowKey, { traceId: event.target.value }, row)
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
                              patchDraft(rowKey, { title: event.target.value }, row)
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
                                patchDraft(rowKey, { period: event.target.value }, row)
                              }
                              className="mt-1 block w-full rounded-lg border border-arch-line bg-arch-surface px-2 py-1 text-sm font-normal text-arch-ink"
                            />
                          </label>
                          <label className="block text-xs font-semibold text-arch-green-deep">
                            Статус
                            <select
                              value={draft?.confidence ?? 'needs_verification'}
                              onChange={(event) =>
                                patchDraft(rowKey, {
                                  confidence: event.target.value as Confidence,
                                }, row)
                              }
                              className="mt-1 block w-full rounded-lg border border-arch-line bg-arch-surface px-2 py-1 text-sm font-normal text-arch-ink"
                            >
                              {CONFIDENCE_SELECT_OPTIONS.map((item) => (
                                <option key={item.value} value={item.value}>
                                  {item.label}
                                </option>
                              ))}
                            </select>
                            {draft?.confidence ? (
                              <p className="mt-1 text-[11px] leading-snug text-arch-muted">
                                {CONFIDENCE_SELECT_OPTIONS.find((o) => o.value === draft.confidence)?.hint}
                              </p>
                            ) : null}
                          </label>
                        </div>
                        <label className="mt-2 block text-xs font-semibold text-arch-green-deep">
                          Текст
                          <textarea
                            value={draft?.userMessage ?? ''}
                            onChange={(event) =>
                              patchDraft(rowKey, { userMessage: event.target.value }, row)
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
                              patchDraft(rowKey, { confirmed: event.target.checked }, row)
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
                {tableRows.length}).
              </p>
            </div>
            <button
              type="button"
              disabled={readyCount === 0 || bundles.length === 0}
              onClick={() => {
                downloadExpertFiles(building, bundles, confirmedRows, tracesById)
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
              {bundles.map((bundle) => (
                <li key={bundle.comparisonId}>
                  <code>{bundle.annotationsRelPath}</code> — для{' '}
                  <code>public/explorer/{building.cardId}/</code>
                </li>
              ))}
              <li>
                <code>memory-traces-{building.cardId}.ts</code> — записи для{' '}
                <code>src/data/buildings/{buildingDataFileName(building.cardId)}</code>
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
