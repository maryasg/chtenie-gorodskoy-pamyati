import { Link } from 'react-router-dom'
import { MapView } from '../../components/MapView'

export function MapPageV2() {
  return (
    <div className="v2-container py-10 sm:py-14">
      <div className="mb-8 max-w-2xl">
        <p className="v2-kicker">Platform</p>
        <h1 className="v2-display mt-3 text-3xl sm:text-4xl">Карта объектов</h1>
        <p className="mt-4 text-sm leading-relaxed text-v2-muted normal-case">
          Те же данные и маркеры — новая оболочка. Выберите здание на карте или в списке.
        </p>
        <Link to="/v2" className="v2-btn-text mt-4 inline-flex">
          ← На главную
        </Link>
      </div>
      <div className="v2-panel overflow-hidden p-4 sm:p-5">
        <MapView buildingTo={(id) => `/v2/building/${id}`} />
      </div>
    </div>
  )
}
