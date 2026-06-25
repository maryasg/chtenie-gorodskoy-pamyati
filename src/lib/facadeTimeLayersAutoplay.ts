import type { FacadeTimeSnapshot } from '../data/explorer/explorerManifest'

/** Плавное ускорение/замедление (smoothstep). */
function easeInOut(t: number): number {
  const x = Math.max(0, Math.min(1, t))
  return x * x * (3 - 2 * x)
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t
}

function lerpOpacities(from: number[], to: number[], t: number): number[] {
  return from.map((value, index) => lerp(value, to[index] ?? 0, t))
}

type TimelineSegment = {
  durationMs: number
  from: number[]
  to: number[]
  sliderFrom: number
  sliderTo: number
  thumbFrom: number
  thumbTo: number
}

const M001_HOLD_1840_MS = 1000
const M001_CROSSFADE_MS = 2200
const M001_HOLD_PLATEAU_MS = 800
/** Половина появления 1930 (до 50% = 0.4), затем стартует 2026. */
const M001_1930_HALF_MS = 1100

/** Хореография автопроигрывания для дома Ардовых (MOSCOW_001). */
function moscow001Timeline(layerCount: number): TimelineSegment[] {
  if (layerCount < 4) return []

  return [
    // 1840 — 100%, пауза 1 с
    {
      durationMs: M001_HOLD_1840_MS,
      from: [1, 0, 0, 0],
      to: [1, 0, 0, 0],
      sliderFrom: 0,
      sliderTo: 0,
      thumbFrom: 0,
      thumbTo: 1,
    },
    // Одновременно: 1840 → 20%, 1924 → 80%
    {
      durationMs: M001_CROSSFADE_MS,
      from: [1, 0, 0, 0],
      to: [0.2, 0.8, 0, 0],
      sliderFrom: 0,
      sliderTo: 33.33,
      thumbFrom: 1,
      thumbTo: 1,
    },
    {
      durationMs: M001_HOLD_PLATEAU_MS,
      from: [0.2, 0.8, 0, 0],
      to: [0.2, 0.8, 0, 0],
      sliderFrom: 33.33,
      sliderTo: 33.33,
      thumbFrom: 1,
      thumbTo: 1,
    },
    // 1930 до 50% (0.4)
    {
      durationMs: M001_1930_HALF_MS,
      from: [0.2, 0.8, 0, 0],
      to: [0.2, 0.8, 0.4, 0],
      sliderFrom: 33.33,
      sliderTo: 50,
      thumbFrom: 1,
      thumbTo: 1,
    },
    // 1930 50%→80% и одновременно 2026 → 100%
    {
      durationMs: M001_1930_HALF_MS,
      from: [0.2, 0.8, 0.4, 0],
      to: [0.2, 0.8, 0.8, 1],
      sliderFrom: 50,
      sliderTo: 100,
      thumbFrom: 1,
      thumbTo: 1,
    },
    {
      durationMs: M001_HOLD_PLATEAU_MS,
      from: [0.2, 0.8, 0.8, 1],
      to: [0.2, 0.8, 0.8, 1],
      sliderFrom: 100,
      sliderTo: 100,
      thumbFrom: 1,
      thumbTo: 1,
    },
    // Сброс цикла: всё в прозрачность, ползунок на 1840, кружок невидим
    {
      durationMs: M001_CROSSFADE_MS,
      from: [0.2, 0.8, 0.8, 1],
      to: [0, 0, 0, 0],
      sliderFrom: 100,
      sliderTo: 0,
      thumbFrom: 1,
      thumbTo: 0,
    },
    {
      durationMs: 150,
      from: [0, 0, 0, 0],
      to: [0, 0, 0, 0],
      sliderFrom: 0,
      sliderTo: 0,
      thumbFrom: 0,
      thumbTo: 0,
    },
  ]
}

export type StackedAutoplayFrame = {
  opacities: number[]
  sliderPct: number
  sliderThumbOpacity: number
  emphasisIndex: number
}

function timelineDurationMs(segments: TimelineSegment[]): number {
  return segments.reduce((sum, segment) => sum + segment.durationMs, 0)
}

function sampleTimeline(
  segments: TimelineSegment[],
  elapsedMs: number,
): { opacities: number[]; sliderPct: number; thumbOpacity: number; emphasisIndex: number } {
  const cycleMs = timelineDurationMs(segments)
  const cycleElapsed = ((elapsedMs % cycleMs) + cycleMs) % cycleMs

  let cursor = 0
  for (let index = 0; index < segments.length; index += 1) {
    const segment = segments[index]
    const nextCursor = cursor + segment.durationMs
    if (cycleElapsed < nextCursor || index === segments.length - 1) {
      const localT = segment.durationMs > 0 ? (cycleElapsed - cursor) / segment.durationMs : 1
      const eased = easeInOut(Math.max(0, Math.min(1, localT)))
      return {
        opacities: lerpOpacities(segment.from, segment.to, eased),
        sliderPct: lerp(segment.sliderFrom, segment.sliderTo, eased),
        thumbOpacity: lerp(segment.thumbFrom, segment.thumbTo, eased),
        emphasisIndex: emphasisLayerIndex(
          lerpOpacities(segment.from, segment.to, eased),
        ),
      }
    }
    cursor = nextCursor
  }

  const last = segments[segments.length - 1]
  return {
    opacities: last.to,
    sliderPct: last.sliderTo,
    thumbOpacity: last.thumbTo,
    emphasisIndex: emphasisLayerIndex(last.to),
  }
}

function emphasisLayerIndex(opacities: number[]): number {
  for (let index = opacities.length - 1; index >= 0; index -= 1) {
    if (opacities[index] > 0.05) return index
  }
  return 0
}

export function usesStackedAutoplay(cardId?: string, layerCount?: number): boolean {
  return cardId === 'MOSCOW_001' && (layerCount ?? 0) >= 4
}

export function stackedAutoplayCycleMs(cardId: string, layerCount: number): number {
  if (!usesStackedAutoplay(cardId, layerCount)) return 0
  return timelineDurationMs(moscow001Timeline(layerCount))
}

export function computeStackedAutoplayFrame(
  layers: FacadeTimeSnapshot[],
  elapsedMs: number,
): StackedAutoplayFrame {
  const segments = moscow001Timeline(layers.length)
  const sample = sampleTimeline(segments, elapsedMs)
  return {
    opacities: sample.opacities,
    sliderPct: sample.sliderPct,
    sliderThumbOpacity: sample.thumbOpacity,
    emphasisIndex: sample.emphasisIndex,
  }
}

export function stackedAutoplayYearLabel(
  layers: FacadeTimeSnapshot[],
  emphasisIndex: number,
): string {
  const layer = layers[emphasisIndex] ?? layers[0]
  return layer?.label ?? layer?.year ?? ''
}
