import { MapView } from '../components/MapView'

export function MapPage() {
  return (
    <div>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight text-arch-green-deep">Москва</h1>
      <p className="mb-1 max-w-2xl text-sm text-arch-muted">Карта архитектурных объектов</p>
      <p className="mb-4 max-w-2xl text-sm text-arch-muted">
        Выберите здание на карте или в списке.
      </p>
      <div className="arch-section p-0 overflow-hidden">
        <MapView />
      </div>
    </div>
  )
}
