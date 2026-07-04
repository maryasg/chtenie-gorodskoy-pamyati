import { Link } from 'react-router-dom'
import { MapView } from '../../components/MapView'

export function MapPageV2() {
  return (
    <div className="v2-container py-10 sm:py-14">
      <div className="mb-8 max-w-2xl">
        <p className="v2-kicker">Platform</p>
        <h1 className="v2-hero-title mt-3 text-3xl sm:text-4xl">Карта объектов</h1>
        <p className="mt-4 text-base leading-relaxed text-v2-muted">
          Те же данные и маркеры — новая оболочка страницы. Выберите здание на карте или в списке.
        </p>
        <Link to="/v2" className="mt-4 inline-block text-sm font-medium text-v2-blue hover:underline">
          ← На главную v2
        </Link>
      </div>
      <div className="v2-card overflow-hidden p-0">
        <MapView buildingTo={(id) => `/v2/building/${id}`} />
      </div>
    </div>
  )
}
