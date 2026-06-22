import { MapView } from '../components/MapView'

export function MapPage() {
  return (
    <div className="space-y-4">
      <header className="arch-section border-arch-green/20 bg-gradient-to-br from-arch-green-soft to-arch-surface">
        <h1 className="text-2xl font-semibold tracking-tight text-arch-green-deep">
          Москва. Карта архитектурных объектов
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-arch-muted">
          Выберите здание на карте или в списке.
        </p>
      </header>
      <div className="arch-section p-0 overflow-hidden">
        <MapView />
      </div>
    </div>
  )
}
