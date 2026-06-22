import { MapView } from '../components/MapView'

export function MapPage() {
  return (
    <div>
      <p className="arch-kicker mb-1">Москва</p>
      <h1 className="mb-2 text-3xl font-semibold tracking-tight text-arch-green sm:text-4xl">
        Карта архитектурных объектов
      </h1>
      <p className="mb-4 max-w-2xl text-sm text-arch-muted">
        Выберите здание на карте или в списке.
      </p>
      <div className="arch-section p-0 overflow-hidden">
        <MapView />
      </div>
    </div>
  )
}
