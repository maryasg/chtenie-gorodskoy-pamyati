import type { MapStatus } from '../types/building'

/** Подписи под картой — только активные статусы объектов. */
export const MAP_LEGEND_STATUSES: MapStatus[] = ['verified', 'in_preparation']

export const MAP_STATUS_META: Record<
  MapStatus,
  { label: string; color: string; marker: string }
> = {
  verified: { label: 'Достоверные данные', color: '#16a34a', marker: '#15803d' },
  preliminary_reading: {
    label: 'Предварительное чтение',
    color: '#ca8a04',
    marker: '#a16207',
  },
  in_preparation: { label: 'В подготовке', color: '#2563eb', marker: '#1d4ed8' },
  no_data: { label: 'Нет данных', color: '#6b7280', marker: '#4b5563' },
}
