import type { Confidence } from '../types/building'

const STYLES: Record<Confidence, string> = {
  confirmed: 'bg-emerald-100 text-emerald-900 border-emerald-300',
  probable: 'bg-slate-100 text-slate-800 border-slate-300',
  needs_verification: 'bg-amber-100 text-amber-900 border-amber-300',
  typological_hypothesis: 'bg-violet-100 text-violet-900 border-violet-300',
}

const LABELS: Record<Confidence, string> = {
  confirmed: 'Подтверждено',
  probable: 'Вероятно',
  needs_verification: 'Требует проверки',
  typological_hypothesis: 'Типологическая гипотеза',
}

export function ConfidenceBadge({ level }: { level: Confidence }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${STYLES[level]}`}
    >
      {LABELS[level]}
    </span>
  )
}
