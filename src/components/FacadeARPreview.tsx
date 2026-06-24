import type { Building } from '../types/building'
import type { ArchiviewBuildingAssets } from '../data/explorer/archiviewAssets'
import { ArchiviewFacadePanel } from './ArchiviewFacadePanel'

type Props = {
  building: Building
  archiview: ArchiviewBuildingAssets
}

/** Симуляция AR без камеры: полевое фото в «экране телефона» + подсветка Archiview. */
export function FacadeARPreview({ building, archiview }: Props) {
  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-arch-green/25 bg-arch-green-soft p-4 text-sm leading-relaxed text-arch-green-deep">
        <strong>AR-preview (без камеры).</strong> Полевое фото в том ракурсе, в котором снимали на
        месте. Подсветка экспертных заметок Archiview: наведите на зону — краткая подсказка внизу
        экрана, <strong>клик</strong> — полная карточка по центру. Сравнение «до/после» и слои
        времени — в блоке «Сравнение фотоматериалов» на карточке здания.
      </div>

      <p className="text-center text-sm text-arch-muted">
        Исходный ракурс с улицы — как в видоискателе. <strong>Наведите</strong> на область — подсказка
        внизу экрана; <strong>клик</strong> — полная карточка.
      </p>

      <div className="mx-auto w-full max-w-[min(920px,98vw)]">
        <div
          className="rounded-[3rem] border-[12px] border-neutral-800 bg-neutral-900 px-2.5 pb-4 pt-2.5 shadow-2xl"
          role="img"
          aria-label="Симуляция экрана телефона с полевым фото и подсветкой зон"
        >
          <div className="mx-auto mb-2.5 h-6 w-36 rounded-full bg-neutral-950/90" aria-hidden />

          <div className="overflow-hidden rounded-[2.25rem] bg-arch-green-deep ring-1 ring-arch-surface/10">
            <div className="flex items-center justify-between border-b border-arch-surface/10 bg-arch-green-deep px-4 py-2 text-xs text-arch-surface/70">
              <span>AR · симуляция</span>
              {archiview.modernPhotoYear ? (
                <span className="tabular-nums">полевое фото · {archiview.modernPhotoYear}</span>
              ) : null}
            </div>

            <div className="relative aspect-[9/16] w-full overflow-hidden">
              <div className="absolute inset-0">
                <ArchiviewFacadePanel
                  assets={archiview}
                  building={building}
                  variant="ar"
                  embeddedAr
                  hideIntro
                />
              </div>
            </div>
          </div>

          <div className="mx-auto mt-3 h-1.5 w-32 rounded-full bg-neutral-600" aria-hidden />
        </div>
      </div>
    </div>
  )
}
