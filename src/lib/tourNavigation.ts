import { PILOT_TOUR } from '../data/tour'

export type TourNavLink = {
  to: string
  label: string
  ariaLabel: string
}

/** Следующая точка маршрута пилота; после последней — на карту. */
export function getNextTourNavLink(currentBuildingId: string): TourNavLink {
  const idx = PILOT_TOUR.findIndex((stop) => stop.buildingId === currentBuildingId)

  if (idx === -1 || idx >= PILOT_TOUR.length - 1) {
    return {
      to: '/',
      label: 'На карту →',
      ariaLabel: 'Вернуться на карту Москвы',
    }
  }

  const next = PILOT_TOUR[idx + 1]
  return {
    to: `/building/${next.buildingId}`,
    label: 'Далее →',
    ariaLabel: `Следующая точка маршрута: ${next.title}`,
  }
}
