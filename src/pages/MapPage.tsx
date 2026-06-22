import { MapView } from '../components/MapView'

export function MapPage() {
  return (
    <div className="space-y-4">
      <header className="arch-section border-arch-green/20 bg-gradient-to-br from-arch-green-soft to-arch-surface">
        <p className="text-3xl font-bold tracking-tight text-arch-green-deep sm:text-4xl">Москва</p>
        <h1 className="mt-1 text-sm font-medium text-arch-muted sm:text-base">Карта архитектурных объектов</h1>
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
