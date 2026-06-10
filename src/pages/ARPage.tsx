import { Link, useParams } from 'react-router-dom'
import { getBuildingById } from '../data/buildings'
import { FacadeARPreview } from '../components/FacadeARPreview'
import { FacadeHotspotViewer } from '../components/FacadeHotspotViewer'
import { getArchiviewAssets } from '../data/explorer/archiviewAssets'

export function ARPage() {
  const { id } = useParams<{ id: string }>()
  const building = id ? getBuildingById(id) : undefined
  const archiview = building ? getArchiviewAssets(building.id) : undefined

  if (!building) {
    return <p>Здание не найдено.</p>
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to={`/building/${building.id}`} className="text-sm text-stone-500 hover:text-stone-800">
          ← Карточка здания
        </Link>
        <h1 className="mt-2 text-2xl font-semibold">AR-preview: {building.name}</h1>
        <p className="mt-1 text-sm text-stone-600">{building.address}</p>
      </div>

      {archiview?.labelingLayout === 'side_by_side' ? (
        <div className="rounded-lg border border-arch-line bg-arch-surface p-4 text-sm leading-relaxed text-arch-ink/80">
          Для этого здания AR-preview не показывается: фотоматериалы сняты с разных ракурсов и не
          выпрямлялись в единую плоскость. В карточке используется side-by-side-разметка, где важно
          сравнить, читается ли вывеска на каждом снимке.
        </div>
      ) : archiview ? (
        <FacadeARPreview building={building} archiview={archiview} />
      ) : (
        <>
          <div className="rounded-lg border border-stone-200 bg-stone-50 p-4 text-sm text-stone-700">
            Для этого здания пока нет экспорта Archiview. Ниже — схема hotspots; после разметки в
            Archiview и Push на сайт здесь появится режим «слои времени» с реальными фото.
          </div>
          <FacadeHotspotViewer building={building} />
        </>
      )}
    </div>
  )
}
