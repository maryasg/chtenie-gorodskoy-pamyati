import { MapView } from '../components/MapView'

export function MapPage() {
  return (
    <div>
      <h1 className="mb-2 text-2xl font-semibold">Карта пилота</h1>
      <p className="mb-4 text-sm text-stone-600">
        Четыре здания исторического центра Москвы. Статусы показывают охват платформы.
        Выберите здание на карте или в списке.
      </p>
      <MapView />
    </div>
  )
}
