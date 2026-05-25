import { useEffect, useRef } from 'react'
import L from 'leaflet'
import { Link } from 'react-router-dom'
import { BUILDINGS, MAP_CENTER, MAP_ZOOM } from '../data/buildings'
import { MAP_STATUS_META } from '../data/statuses'

import iconRetina from 'leaflet/dist/images/marker-icon-2x.png'
import icon from 'leaflet/dist/images/marker-icon.png'
import shadow from 'leaflet/dist/images/marker-shadow.png'

// @ts-expect-error leaflet default icon paths
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({ iconRetinaUrl: iconRetina, iconUrl: icon, shadowUrl: shadow })

function coloredIcon(color: string) {
  return L.divIcon({
    className: '',
    html: `<div style="background:${color};width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.35)"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })
}

export function MapView() {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)

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
        `<strong>${b.name}</strong><br/>${meta.label}<br/><a href="${import.meta.env.BASE_URL}building/${b.id}">Открыть карточку</a>`,
      )
    })

    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

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
      <ul className="grid gap-2 sm:grid-cols-2">
        {BUILDINGS.map((b) => (
          <li key={b.id}>
            <Link
              to={`/building/${b.id}`}
              className="block rounded-lg border border-stone-200 bg-white p-3 hover:border-stone-400"
            >
              <span className="font-medium">{b.name}</span>
              <span className="mt-1 block text-xs text-stone-500">{b.address}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
