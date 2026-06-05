import { MapView } from '../components/MapView'

export function MapPage() {
  return (
    <div>
      <p className="arch-kicker mb-1">Пилот Москва</p>
      <h1 className="mb-2 text-2xl font-semibold tracking-tight text-arch-green-deep">Карта пилота</h1>
      <p className="mb-4 max-w-2xl text-sm text-arch-muted">
        Четыре здания исторического центра. Статусы показывают охват платформы. Выберите здание на
        карте или в списке.
      </p>
      <div className="arch-section p-0 overflow-hidden">
        <MapView />
      </div>
    </div>
  )
}
