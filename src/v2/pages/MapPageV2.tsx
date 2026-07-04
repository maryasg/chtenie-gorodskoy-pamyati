import { MapView } from '../../components/MapView'

export function MapPageV2() {
  return (
    <div className="space-y-4">
      <header>
        <p className="v2-kicker">Карта</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">Архитектурные объекты</h1>
        <p className="mt-2 text-sm text-v2-muted">
          Пока используем ту же карту и данные — меняется только оболочка страницы.
        </p>
      </header>
      <div className="v2-card overflow-hidden p-0">
        <MapView />
      </div>
    </div>
  )
}
