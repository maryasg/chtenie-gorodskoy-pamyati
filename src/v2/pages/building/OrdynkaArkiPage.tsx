import { Link } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import { MOSCOW_001 } from '../../../data/buildings/moscow001'
import { ArchiviewFacadePanel } from '../../../components/ArchiviewFacadePanel'
import { FacadeTimeLayers } from '../../../components/FacadeTimeLayers'
import { getArchiviewAssets } from '../../../data/explorer/archiviewAssets'
import {
  fetchExplorerManifest,
  manifestEntryToAssets,
  resolveDefaultComparisonId,
  type ExplorerManifest,
} from '../../../data/explorer/explorerManifest'
import { ArchiviewComparisonPicker } from '../../../components/ArchiviewComparisonPicker'
import { getConfidenceInfo } from '../../../data/confidenceGuide'
import type { Confidence } from '../../../types/building'
import { V2SquareMark } from '../../components/V2SquareMark'
import '../../arki-theme.css'

const BUILDING = MOSCOW_001
const OBJECT_REF = 'MOSCOW_001 · 77-04-A017'

const INSPECTOR_LAYERS = [
  { year: '1840', title: 'План усадьбы', sub: 'РГАДА' },
  { year: '1924', title: 'Архивное фото', sub: 'PastVu · ГИМ' },
  { year: '1930–36', title: 'Строительство в лесах', sub: 'Архив ЦИГИ' },
  { year: '2026', title: 'Полевая съёмка', sub: 'Archiview' },
]

const OVERLAY_GROUPS = [
  {
    code: 'L·01',
    title: 'Утраченные элементы',
    sub: 'Существовали до реконструкции · сегодня не видны',
    count: 3,
    active: true,
    dot: '#e31e24',
  },
  {
    code: 'K·02',
    title: 'Сохранившиеся из прошлых слоёв',
    sub: 'Уцелели через все перестройки',
    count: 4,
    active: false,
    dot: '#059669',
  },
  {
    code: 'A·03',
    title: 'Добавленные при реконструкции',
    sub: 'Возникли после 1938 · видны сегодня',
    count: 3,
    active: false,
    dot: '#0284c7',
  },
]

function confidencePct(level: Confidence, numeric?: number): string {
  if (numeric != null && numeric > 0) {
    return `${Math.round(numeric * 100)}%`
  }
  const fallback: Record<Confidence, string> = {
    confirmed: '92%',
    highly_probable: '78%',
    probable: '60%',
    needs_verification: '45%',
    typological_hypothesis: '40%',
  }
  return fallback[level]
}

function LayerCheckbox({ on }: { on: boolean }) {
  return <span className={on ? 'arki-check arki-check--on' : 'arki-check arki-check--off'} aria-hidden />
}

export function OrdynkaArkiPage() {
  const building = BUILDING
  const archiview = getArchiviewAssets(building.id)
  const [manifest, setManifest] = useState<ExplorerManifest | null>(null)
  const [selectedComparisonId, setSelectedComparisonId] = useState('')
  const [photoOpacity, setPhotoOpacity] = useState(35)
  const [layerOn, setLayerOn] = useState([true, false, false, true])

  useEffect(() => {
    if (!archiview?.cardId) return
    let cancelled = false
    fetchExplorerManifest(archiview.cardId).then((data) => {
      if (cancelled) return
      setManifest(data)
      if (data?.comparisons?.length) {
        setSelectedComparisonId(resolveDefaultComparisonId(data))
      }
    })
    return () => {
      cancelled = true
    }
  }, [archiview?.cardId])

  const displayAssets = useMemo(() => {
    if (!archiview) return undefined
    if (!manifest || manifest.comparisons.length <= 1) return archiview
    const entry =
      manifest.comparisons.find((c) => c.comparisonId === selectedComparisonId) ??
      manifest.comparisons.find((c) => c.comparisonId === resolveDefaultComparisonId(manifest)) ??
      manifest.comparisons[0]
    return manifestEntryToAssets(archiview.cardId, archiview.buildingId, entry, archiview)
  }, [archiview, manifest, selectedComparisonId])

  if (!displayAssets) {
    return (
      <div className="v2-container py-10">
        <p className="text-v2-muted">Нет данных Archiview для этой карточки.</p>
      </div>
    )
  }

  const traceLabels = building.memoryTraces.slice(0, 7).map((t, i) => ({
    id: t.id,
    label: `L${i + 1} · ${t.title.length > 28 ? `${t.title.slice(0, 28)}…` : t.title}`,
  }))

  const archiveCount = building.photos.filter((p) => p.type === 'archive').length
  const expertiseCount = building.verification?.officialExpertise?.length ?? 0
  const fieldCount = 1
  const hypothesisCount = building.memoryTraces.filter(
    (t) => t.confidence === 'typological_hypothesis' || t.confidence === 'needs_verification',
  ).length

  return (
    <div
      className="arki-page pb-16"
      style={{ ['--arki-photo-opacity' as string]: String(photoOpacity / 100) }}
    >
      {/* Header */}
      <header className="arki-border border-t-0 border-x-0">
        <div className="v2-container grid gap-0 lg:grid-cols-[1fr_auto]">
          <div className="arki-border border-t-0 border-l-0 border-r-0 p-4 sm:p-6 lg:border-r">
            <div className="flex flex-wrap items-center gap-2">
              <span className="arki-badge-verified">Verified</span>
              <span className="arki-mono text-[var(--arki-muted)]">Object ID · {OBJECT_REF}</span>
            </div>
            <h1 className="arki-serif mt-4 text-4xl leading-[1.05] sm:text-5xl">{building.name}</h1>
            <p className="arki-mono mt-3 text-[var(--arki-muted)] normal-case">
              {building.address} · {building.lat.toFixed(4)}° N, {building.lng.toFixed(4)}° E
            </p>
          </div>
          <div className="flex flex-col justify-between gap-4 p-4 sm:p-6">
            <Link to="/v2/map" className="arki-mono self-end text-[var(--arki-ink)] hover:text-[var(--arki-red)]">
              ← Карта города
            </Link>
            <div>
              <p className="arki-mono text-[var(--arki-muted)]">Датировка</p>
              <ul className="arki-mono mt-2 space-y-1 text-[11px] normal-case">
                <li>Палаты · сер. XVIII</li>
                <li>Усадьба · XVIII–XIX</li>
                <li className="text-[var(--arki-red)]">Надстройка · 1938</li>
              </ul>
              <p className="arki-mono mt-3 text-[var(--arki-red)]">
                {building.timeline.length} слоёв · {building.sources.length} источника
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Hero grid */}
      <section className="v2-container">
        <div className="grid border border-[var(--arki-line)] lg:grid-cols-[minmax(200px,240px)_1fr_minmax(220px,280px)]">
          <aside className="border-b border-[var(--arki-line)] p-4 lg:border-r lg:border-b-0">
            <p className="arki-mono text-[var(--arki-muted)]">Legend · фрагмент 01A</p>
            <p className="arki-mono mt-2 text-[var(--arki-red)]">Надстройка 1938</p>
            <p className="mt-3 text-[11px] leading-relaxed normal-case text-[var(--arki-muted)]">
              Заложенный проём · сер. XIX — линии L показывают утраты; K — сохранившиеся элементы;
              A — добавления советского слоя.
            </p>
            <ul className="mt-4 space-y-2">
              {traceLabels.map((t) => (
                <li key={t.id} className="arki-mono text-[10px] text-[var(--arki-muted)] normal-case">
                  {t.label}
                </li>
              ))}
            </ul>
          </aside>

          <div className="arki-frame m-3 min-h-[280px] bg-white p-2 sm:min-h-[360px]">
            <img
              src={displayAssets.labeledFacadeUrl}
              alt="Чертёжная разметка фасада"
              className="h-full w-full object-contain"
            />
          </div>

          <aside className="border-t border-[var(--arki-line)] p-4 lg:border-t-0 lg:border-l">
            <p className="arki-mono text-[var(--arki-muted)]">Inspector · Слои</p>
            <div className="mt-3">
              {INSPECTOR_LAYERS.map((layer, i) => (
                <div key={layer.year} className="arki-layer-row">
                  <button
                    type="button"
                    className="flex items-start gap-2 text-left"
                    onClick={() =>
                      setLayerOn((prev) => prev.map((v, j) => (j === i ? !v : v)))
                    }
                  >
                    <LayerCheckbox on={layerOn[i]} />
                  </button>
                  <div>
                    <p className="arki-mono font-semibold text-[var(--arki-ink)]">{layer.year}</p>
                    <p className="mt-0.5 text-[10px] normal-case text-[var(--arki-muted)]">{layer.title}</p>
                    <p className="arki-mono mt-0.5 text-[9px] text-[var(--arki-muted)]">{layer.sub}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 border border-[var(--arki-line)] p-3">
              <p className="arki-mono text-[var(--arki-muted)]">Кроссфейд · 1840 → 2026</p>
              <FacadeTimeLayers building={building} archiview={displayAssets} />
            </div>
          </aside>
        </div>
      </section>

      {/* Facade reading */}
      <section className="v2-container mt-8">
        <div className="grid gap-0 border border-[var(--arki-line)] lg:grid-cols-[1fr_280px]">
          <div className="border-b border-[var(--arki-line)] p-4 lg:border-r lg:border-b-0">
            <p className="arki-mono text-[var(--arki-muted)]">Facade Reading · Overlay Method</p>
            <h2 className="arki-serif mt-2 text-2xl sm:text-3xl">
              Современное фото + чертёжная разметка
            </h2>
            <p className="mt-2 max-w-2xl text-[11px] leading-relaxed normal-case text-[var(--arki-muted)]">
              Базовый снимок гасится до призрака · поверх — группы обвёртки, каждая со своим типом
              линии.
            </p>
            {manifest && manifest.comparisons.length > 1 ? (
              <div className="mt-3">
                <ArchiviewComparisonPicker
                  manifest={manifest}
                  selectedId={selectedComparisonId}
                  onSelect={setSelectedComparisonId}
                />
              </div>
            ) : null}
            <div className="arki-facade-shell mt-4 border border-[var(--arki-line)] bg-white">
              <ArchiviewFacadePanel assets={displayAssets} building={building} />
            </div>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="arki-mono text-[var(--arki-muted)]">Плотность фото</span>
                <div className="mt-2 flex items-center gap-3">
                  <span className="arki-mono text-[9px]">только чертёж</span>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={photoOpacity}
                    onChange={(e) => setPhotoOpacity(Number(e.target.value))}
                    className="w-full accent-[var(--arki-red)]"
                  />
                  <span className="arki-mono text-[9px]">только фото</span>
                </div>
                <p className="arki-mono mt-1 text-[var(--arki-red)]">{photoOpacity}%</p>
              </label>
              <div className="border border-[var(--arki-line)] p-3">
                <p className="arki-mono text-[var(--arki-muted)]">Registration Filter</p>
                <ul className="mt-2 space-y-1 text-[10px] normal-case text-[var(--arki-muted)]">
                  <li>grayscale 70%</li>
                  <li>contrast 1.05</li>
                  <li>opacity {photoOpacity}%</li>
                  <li>blend multiply</li>
                </ul>
              </div>
            </div>
          </div>

          <aside className="p-4">
            <p className="arki-mono text-[var(--arki-muted)]">Overlay Groups</p>
            <p className="arki-mono mt-1 text-[9px] text-[var(--arki-muted)]">Три вида линий · один снимок</p>
            <div className="mt-4">
              {OVERLAY_GROUPS.map((g) => (
                <div key={g.code} className="arki-overlay-group">
                  <div className="flex gap-2">
                    <V2SquareMark active={g.active} innerColor={g.dot} />
                    <div>
                      <p className="arki-mono font-semibold text-[var(--arki-ink)]">{g.code}</p>
                      <p className="arki-mono mt-1 text-[10px] font-semibold normal-case text-[var(--arki-ink)]">
                        {g.title}
                      </p>
                      <p className="mt-1 text-[10px] normal-case text-[var(--arki-muted)]">{g.sub}</p>
                      <p className="arki-mono mt-2 text-[9px] text-[var(--arki-muted)]">
                        {g.count} обвёртки
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </section>

      {/* Reading */}
      <section className="v2-container mt-8 border border-[var(--arki-line)] p-6 sm:p-8">
        <h2 className="arki-serif text-2xl">// Чтение фасада</h2>
        <p className="arki-serif-italic mt-4 max-w-3xl text-lg leading-relaxed text-[var(--arki-muted)]">
          {building.summary}
        </p>

        <div className="mt-8 grid gap-4 border-t border-[var(--arki-line)] pt-6 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: 'Архивные фотоматериалы', n: archiveCount },
            { label: 'Официальная экспертиза', n: expertiseCount },
            { label: 'Полевые наблюдения', n: fieldCount },
            { label: 'Гипотезы', n: hypothesisCount },
          ].map((item) => (
            <div key={item.label} className="arki-border p-3">
              <p className="arki-mono text-[var(--arki-muted)]">{item.label}</p>
              <p className="arki-serif mt-2 text-3xl">{item.n}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Dossier */}
      <section className="v2-container mt-8 mb-12">
        <h2 className="arki-mono mb-4 text-[var(--arki-ink)]">Dossier // Исторические слои</h2>
        <div className="overflow-x-auto border border-[var(--arki-line)] bg-white">
          <table className="arki-table">
            <thead>
              <tr>
                <th>Период</th>
                <th>Слой</th>
                <th>Достоверность</th>
                <th>Что изменилось</th>
                <th>Видно сегодня</th>
                <th>Источник</th>
              </tr>
            </thead>
            <tbody>
              {building.timeline.map((row) => {
                const info = getConfidenceInfo(row.confidence)
                return (
                  <tr key={row.id}>
                    <td className="arki-mono whitespace-nowrap">{row.period}</td>
                    <td className="font-medium normal-case">{row.title}</td>
                    <td className="whitespace-nowrap">
                      <span className="text-[var(--arki-red)]">{confidencePct(row.confidence)}</span>
                      <span className="ml-1 text-[var(--arki-muted)]">{info.label}</span>
                    </td>
                    <td className="max-w-xs normal-case text-[var(--arki-muted)]">{row.whatChanged}</td>
                    <td className="max-w-xs normal-case text-[var(--arki-muted)]">{row.visibleToday}</td>
                    <td className="max-w-[10rem] text-[10px] normal-case text-[var(--arki-muted)]">
                      {row.source}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        <div className="mt-6 grid gap-6 border border-[var(--arki-line)] p-4 sm:grid-cols-2">
          <div>
            <h3 className="arki-mono text-[var(--arki-muted)]">Сохранившиеся элементы</h3>
            <ul className="mt-3 space-y-1 text-[11px] normal-case text-[var(--arki-muted)]">
              {building.artifacts.map((a) => (
                <li key={a.id}>— {a.title}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="arki-mono text-[var(--arki-muted)]">Источники</h3>
            <ul className="mt-3 space-y-1 text-[11px] normal-case text-[var(--arki-muted)]">
              {building.sources.slice(0, 6).map((s) => (
                <li key={s.id}>
                  {s.url ? (
                    <a href={s.url} target="_blank" rel="noreferrer" className="underline hover:text-[var(--arki-red)]">
                      {s.name}
                    </a>
                  ) : (
                    s.name
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <footer className="arki-mono mt-8 flex flex-wrap justify-between gap-2 border-t border-[var(--arki-line)] pt-4 text-[var(--arki-muted)]">
          <span>Project ARCHITECTOR</span>
          <span>Document release 2.6.0 · Node MOW-ORD-17</span>
        </footer>
      </section>
    </div>
  )
}
