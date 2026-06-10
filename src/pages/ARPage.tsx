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
      <header className="arch-section border-arch-green/20 bg-gradient-to-br from-arch-green-soft to-arch-surface">
        <Link to={`/building/${building.id}`} className="text-sm font-medium text-arch-green-light hover:text-arch-green-deep">
          ← Карточка здания
        </Link>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-arch-green-deep">AR-preview: {building.name}</h1>
        <p className="mt-1 text-sm text-arch-muted">{building.address}</p>
      </header>

      {archiview?.labelingLayout === 'side_by_side' ? (
        <div className="arch-section text-sm leading-relaxed text-arch-ink/80">
          Для этого здания AR-preview не показывается: фотоматериалы сняты с разных ракурсов и не
          выпрямлялись в единую плоскость. В карточке используется side-by-side-разметка, где важно
          сравнить, читается ли вывеска на каждом снимке.
        </div>
      ) : archiview ? (
        <FacadeARPreview building={building} archiview={archiview} />
      ) : (
        <>
          <div className="arch-section text-sm leading-relaxed text-arch-ink/80">
            Для этого здания пока нет экспорта Archiview. Ниже — схема hotspots; после разметки в
            Archiview и Push на сайт здесь появится режим «слои времени» с реальными фото.
          </div>
          <FacadeHotspotViewer building={building} />
        </>
      )}
    </div>
  )
}
