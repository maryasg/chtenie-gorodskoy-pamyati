import type { Building } from '../types/building'
import type { ArchiviewBuildingAssets } from '../data/explorer/archiviewAssets'
import { ArchiviewFacadePanel } from './ArchiviewFacadePanel'

type Props = {
  building: Building
  archiview: ArchiviewBuildingAssets
}

/** Симуляция AR без камеры: исходное полевое фото + подсветка Archiview. */
export function FacadeARPreview({ building, archiview }: Props) {
  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-arch-green/25 bg-arch-green-soft p-4 text-sm leading-relaxed text-arch-green-deep">
        <strong>AR-preview (без камеры).</strong> Показано исходное современное фото в том ракурсе,
        в котором снимали на месте — до выпрямления и обрезки. Поверх него — подсветка кураторских
        заметок Archiview: наведите на номер или зону, кликните — полная карточка с источниками.
        Сравнение «до/после» и режим «слои времени» — в блоке «Сравнение фотоматериалов» на
        карточке здания.
      </div>

      <div className="overflow-hidden rounded-2xl border border-arch-line bg-arch-green-deep shadow-lg">
        <div className="flex items-center justify-between border-b border-arch-green/60 bg-arch-green-deep px-4 py-2 text-xs text-arch-surface/75">
          <span>Режим: дополненная реальность · симуляция</span>
          {archiview.modernPhotoYear && (
            <span className="tabular-nums">полевое фото · {archiview.modernPhotoYear}</span>
          )}
        </div>

        <div className="bg-arch-green-deep p-3 sm:p-4">
          <div className="relative mx-auto max-w-4xl">
            <div
              className="pointer-events-none absolute inset-3 z-10 rounded-lg border-2 border-white/25"
              aria-hidden
            />
            <div
              className="pointer-events-none absolute left-5 top-5 z-10 h-6 w-6 border-l-2 border-t-2 border-arch-gold/80"
              aria-hidden
            />
            <div
              className="pointer-events-none absolute right-5 top-5 z-10 h-6 w-6 border-r-2 border-t-2 border-arch-gold/80"
              aria-hidden
            />
            <div
              className="pointer-events-none absolute bottom-5 left-5 z-10 h-6 w-6 border-b-2 border-l-2 border-arch-gold/80"
              aria-hidden
            />
            <div
              className="pointer-events-none absolute bottom-5 right-5 z-10 h-6 w-6 border-b-2 border-r-2 border-arch-gold/80"
              aria-hidden
            />
            <ArchiviewFacadePanel assets={archiview} building={building} variant="ar" />
          </div>
        </div>
      </div>
    </div>
  )
}
