import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import { Link } from 'react-router-dom'
import { BUILDINGS } from '../data/buildings'
import type { Building } from '../types/building'
import { MAP_LEGEND_STATUSES, MAP_STATUS_META } from '../data/statuses'

import iconRetina from 'leaflet/dist/images/marker-icon-2x.png'
import icon from 'leaflet/dist/images/marker-icon.png'
import shadow from 'leaflet/dist/images/marker-shadow.png'

// @ts-expect-error leaflet default icon paths
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({ iconRetinaUrl: iconRetina, iconUrl: icon, shadowUrl: shadow })

function coloredIcon(color: string, scale = 1) {
  const hit = 30
  const dot = Math.round(14 * scale)
  return L.divIcon({
    className: '',
    html: `<div style="width:${hit}px;height:${hit}px;display:flex;align-items:center;justify-content:center;cursor:pointer"><div style="background:${color};width:${dot}px;height:${dot}px;border-radius:50%;border:2px solid white;box-shadow:0 1px 6px rgba(0,0,0,.4)"></div></div>`,
    iconSize: [hit, hit],
    iconAnchor: [hit / 2, hit / 2],
  })
}

function traceSummary(b: Building): string {
  const titles = b.memoryTraces.slice(0, 4).map((t) => t.title)
  if (titles.length === 0) return 'Следы памяти уточняются'
  const more = b.memoryTraces.length > 4 ? ` … +${b.memoryTraces.length - 4}` : ''
  return titles.join(' · ') + more
}

function buildingPopupHtml(b: Building): string {
  const href = `${import.meta.env.BASE_URL}building/${b.id}`
  return `<div class="arch-map-popup-inner">
    <strong class="arch-map-popup-title">${b.name}</strong>
    <span class="arch-map-popup-address">${b.address}</span>
    <p class="arch-map-popup-summary">${traceSummary(b)}</p>
    <a class="arch-map-popup-link" href="${href}">Открыть карточку →</a>
  </div>`
}

function fitAllBuildings(map: L.Map) {
  const bounds = L.latLngBounds(BUILDINGS.map((b) => [b.lat, b.lng] as L.LatLngTuple))
  const narrow = window.innerWidth < 640
  map.fitBounds(bounds, {
    padding: narrow ? [56, 20] : [44, 44],
    maxZoom: narrow ? 13 : 14,
  })
}

export function MapView() {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const markersRef = useRef<Map<string, L.Marker>>(new Map())
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const container = containerRef.current
    const map = L.map(container, { scrollWheelZoom: false })
    map.attributionControl.setPrefix(false)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright" rel="noopener noreferrer">OpenStreetMap</a>',
    }).addTo(map)

    const markers = new Map<string, L.Marker>()
    BUILDINGS.forEach((b) => {
      const meta = MAP_STATUS_META[b.mapStatus]
      const marker = L.marker([b.lat, b.lng], {
        icon: coloredIcon(meta.marker),
        riseOnHover: true,
      }).addTo(map)

      marker.bindPopup(buildingPopupHtml(b), {
        closeButton: true,
        className: 'arch-map-popup',
        maxWidth: 300,
        minWidth: 220,
        offset: [0, -2],
        autoPan: false,
      })

      marker.on('mouseover', () => setHoveredId(b.id))
      marker.on('mouseout', () => {
        setHoveredId((current) => (current === b.id ? null : current))
      })
      marker.on('click', () => {
        setHoveredId(b.id)
        marker.openPopup()
      })

      markers.set(b.id, marker)
    })

    fitAllBuildings(map)

    const onResize = () => {
      if (!mapRef.current) return
      fitAllBuildings(mapRef.current)
    }
    window.addEventListener('resize', onResize)

    const activateScrollZoom = () => {
      map.scrollWheelZoom.enable()
      container.dataset.zoomActive = 'true'
    }

    const deactivateScrollZoom = () => {
      map.scrollWheelZoom.disable()
      delete container.dataset.zoomActive
    }

    const onContainerClick = () => {
      activateScrollZoom()
    }

    const onDocumentPointerDown = (event: PointerEvent) => {
      if (!container.contains(event.target as Node)) {
        deactivateScrollZoom()
      }
    }

    container.addEventListener('click', onContainerClick)
    document.addEventListener('pointerdown', onDocumentPointerDown)

    mapRef.current = map
    markersRef.current = markers
    return () => {
      window.removeEventListener('resize', onResize)
      container.removeEventListener('click', onContainerClick)
      document.removeEventListener('pointerdown', onDocumentPointerDown)
      map.remove()
      mapRef.current = null
      markers.clear()
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
      }
    })
  }, [hoveredId])

  return (
    <div className="space-y-4">
      <div
        ref={containerRef}
        className="h-[420px] w-full overflow-hidden rounded-xl border border-arch-line shadow-sm data-[zoom-active=true]:ring-2 data-[zoom-active=true]:ring-arch-green/40"
      />
      <div className="flex flex-wrap gap-3 text-sm">
        {MAP_LEGEND_STATUSES.map((key) => {
          const meta = MAP_STATUS_META[key]
          return (
            <span key={key} className="flex items-center gap-1.5">
              <span
                className="inline-block h-3 w-3 rounded-full border border-white shadow"
                style={{ background: meta.marker }}
              />
              {meta.label}
            </span>
          )
        })}
      </div>
      <p className="text-xs text-arch-muted">
        Колёсико мыши прокручивает страницу. Чтобы приблизить карту — сначала кликните по ней, затем
        крутите колёсико. Наведите на точку или на карточку здания ниже — рядом с точкой появится
        краткое описание следов и ссылка на карточку.
      </p>
      <ul className="grid gap-2 sm:grid-cols-2 sm:items-stretch">
        {BUILDINGS.map((b) => (
          <li key={b.id} className="flex min-h-0">
            <Link
              to={`/building/${b.id}`}
              onMouseEnter={() => setHoveredId(b.id)}
              onMouseLeave={() => setHoveredId(null)}
              onFocus={() => setHoveredId(b.id)}
              onBlur={() => setHoveredId(null)}
              className={`flex h-full w-full flex-col rounded-xl border p-3 transition ${
                hoveredId === b.id
                  ? 'border-arch-gold bg-arch-green-soft shadow-sm'
                  : 'border-arch-line bg-arch-surface hover:border-arch-green/40 hover:bg-arch-surface-2/60'
              }`}
            >
              <span className="font-medium text-arch-green-deep">{b.name}</span>
              <span className="mt-1 block text-xs text-arch-muted">{b.address}</span>
              <span className="mt-2 block flex-1 text-xs text-arch-ink/70">{traceSummary(b)}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
