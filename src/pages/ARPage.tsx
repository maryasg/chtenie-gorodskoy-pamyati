import { Link, useParams } from 'react-router-dom'
import { getBuildingById } from '../data/buildings'
import { FacadeHotspotViewer } from '../components/FacadeHotspotViewer'

export function ARPage() {
  const { id } = useParams<{ id: string }>()
  const building = id ? getBuildingById(id) : undefined

  if (!building) {
    return <p>Здание не найдено.</p>
  }

  return (
    <div>
      <Link to={`/building/${building.id}`} className="text-sm text-stone-500">
        ← Карточка здания
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">Симуляция AR</h1>
      <p className="mb-4 text-sm text-stone-600">
        Превью будущего режима: те же hotspots, что на фото фасада. В полевой версии — камера и
        GPS.
      </p>
      <div className="rounded-lg border border-violet-200 bg-violet-50 p-3 text-sm text-violet-900">
        Пилот: оверлей на схеме фасада. Доступ к камере можно добавить при HTTPS-деплое.
      </div>
      <div className="mt-4">
        <FacadeHotspotViewer building={building} />
      </div>
    </div>
  )
}
