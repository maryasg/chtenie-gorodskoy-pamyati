import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import { Link } from 'react-router-dom'
import { BUILDINGS, MAP_CENTER, MAP_ZOOM } from '../data/buildings'
import type { Building } from '../types/building'
import { MAP_STATUS_META } from '../data/statuses'

import iconRetina from 'leaflet/dist/images/marker-icon-2x.png'
import icon from 'leaflet/dist/images/marker-icon.png'
import shadow from 'leaflet/dist/images/marker-shadow.png'

// @ts-expect-error leaflet default icon paths
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({ iconRetinaUrl: iconRetina, iconUrl: icon, shadowUrl: shadow })

function coloredIcon(color: string, scale = 1) {
  const size = Math.round(14 * scale)
  return L.divIcon({
    className: '',
    html: `<div style="background:${color};width:${size}px;height:${size}px;border-radius:50%;border:2px solid white;box-shadow:0 1px 6px rgba(0,0,0,.4)"></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  })
}

function traceSummary(b: Building): string {
  const titles = b.memoryTraces.slice(0, 4).map((t) => t.title)
  if (titles.length === 0) return 'Следы памяти уточняются'
  const more = b.memoryTraces.length > 4 ? ` … +${b.memoryTraces.length - 4}` : ''
  return titles.join(' · ') + more
}

export function MapView() {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const markersRef = useRef<Map<string, L.Marker>>(new Map())
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const map = L.map(containerRef.current).setView(MAP_CENTER, MAP_ZOOM)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
    }).addTo(map)

    BUILDINGS.forEach((b) => {
      const meta = MAP_STATUS_META[b.mapStatus]
      const marker = L.marker([b.lat, b.lng], { icon: coloredIcon(meta.marker) }).addTo(map)
      marker.bindPopup(
        `<strong>${b.name}</strong><br/><span style="font-size:12px;color:#444">${traceSummary(b)}</span><br/><a href="${import.meta.env.BASE_URL}building/${b.id}">Открыть карточку</a>`,
        { closeButton: true },
      )
      markersRef.current.set(b.id, marker)
    })

    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
      markersRef.current.clear()
    }
  }, [])

  useEffect(() => {
    markersRef.current.forEach((marker, id) => {
      const b = BUILDINGS.find((x) => x.id === id)
      if (!b) return
      const meta = MAP_STATUS_META[b.mapStatus]
      const active = id === hoveredId
      marker.setIcon(coloredIcon(meta.marker, active ? 1.45 : 1))
      if (active) {
        marker.openPopup()
        mapRef.current?.panTo([b.lat, b.lng], { animate: true, duration: 0.35 })
      }
    })
  }, [hoveredId])

  return (
    <div className="space-y-4">
      <div ref={containerRef} className="h-[420px] w-full rounded-xl border border-stone-200" />
      <div className="flex flex-wrap gap-3 text-sm">
        {Object.entries(MAP_STATUS_META).map(([key, meta]) => (
          <span key={key} className="flex items-center gap-1.5">
            <span
              className="inline-block h-3 w-3 rounded-full border border-white shadow"
              style={{ background: meta.marker }}
            />
            {meta.label}
          </span>
        ))}
      </div>
      <p className="text-xs text-stone-500">
        Наведите на карточку здания ниже — на карте подсветится точка и названия следов.
      </p>
      <ul className="grid gap-2 sm:grid-cols-2">
        {BUILDINGS.map((b) => (
          <li key={b.id}>
            <Link
              to={`/building/${b.id}`}
              onMouseEnter={() => setHoveredId(b.id)}
              onMouseLeave={() => setHoveredId(null)}
              onFocus={() => setHoveredId(b.id)}
              onBlur={() => setHoveredId(null)}
              className={`block rounded-lg border bg-white p-3 transition ${
                hoveredId === b.id
                  ? 'border-amber-400 bg-amber-50/80 shadow-sm'
                  : 'border-stone-200 hover:border-stone-400'
              }`}
            >
              <span className="font-medium">{b.name}</span>
              <span className="mt-1 block text-xs text-stone-500">{b.address}</span>
              <span className="mt-2 block text-xs text-stone-600">{traceSummary(b)}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
