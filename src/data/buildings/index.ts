import type { Building } from '../../types/building'
import { MOSCOW_001 } from './moscow001'
import { MOSCOW_002 } from './moscow002'
import { MOSCOW_003 } from './moscow003'
import { MOSCOW_004 } from './moscow004'

export const BUILDINGS: Building[] = [MOSCOW_001, MOSCOW_002, MOSCOW_003, MOSCOW_004]

export function getBuildingById(id: string): Building | undefined {
  return BUILDINGS.find((b) => b.id === id)
}

export const MAP_CENTER: [number, number] = [55.7575, 37.6354]
export const MAP_ZOOM = 15
