type V2SquareMarkProps = {
  /** Цвет внутреннего кружка */
  innerColor?: string
  /** Активный слой — красный квадрат с белым центром (как в референсе) */
  active?: boolean
  size?: 'sm' | 'md'
}

export function V2SquareMark({ innerColor = '#9ca3af', active = false, size = 'md' }: V2SquareMarkProps) {
  const box = size === 'sm' ? 'h-3 w-3' : 'h-3.5 w-3.5'
  const dot = size === 'sm' ? 'h-1.5 w-1.5' : 'h-2 w-2'

  if (active) {
    return (
      <span
        className={`inline-flex ${box} shrink-0 items-center justify-center border border-v2-red bg-v2-red`}
        aria-hidden
      >
        <span className={`${dot} bg-white`} />
      </span>
    )
  }

  return (
    <span
      className={`inline-flex ${box} shrink-0 items-center justify-center border border-v2-line bg-v2-surface`}
      aria-hidden
    >
      <span className={`${dot} rounded-full`} style={{ backgroundColor: innerColor }} />
    </span>
  )
}
