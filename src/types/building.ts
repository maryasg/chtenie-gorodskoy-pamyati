export type Confidence =
  | 'confirmed'
  | 'probable'
  | 'needs_verification'
  | 'typological_hypothesis'

export type MapStatus =
  | 'verified'
  | 'preliminary_reading'
  | 'in_preparation'
  | 'no_data'

export interface Hotspot {
  id: string
  label: string
  x: number
  y: number
  width?: number
  height?: number
  traceId?: string
  artifactId?: string
}

export interface MemoryTrace {
  id: string
  type: string
  title: string
  period: string
  confidence: Confidence
  userMessage: string
  imagePath?: string
  imageCaption?: string
  overallConfidence?: number
}

export interface Artifact {
  id: string
  title: string
  period: string
  confidence: Confidence
  location?: string
}

export interface TimelineStage {
  id: string
  period: string
  title: string
  whatChanged: string
  visibleToday: string
  confidence: Confidence
  source?: string
}

export interface PhotoRef {
  id: string
  type: string
  description: string
  url?: string
  status?: string
}

export interface OfficialExpertise {
  title: string
  url: string
  issuedAt?: string
}

export interface MediaReport {
  title: string
  url: string
  outlet?: string
  issuedAt?: string
}

export interface BuildingVerification {
  historicalPhoto: boolean
  historicalPhotoYear?: string
  modernPhotoYear?: string
  officialExpertise?: OfficialExpertise[]
  /** Публикации СМИ как подтверждение фактов (не официальная экспертиза) */
  mediaReports?: MediaReport[]
}

export interface Building {
  id: string
  cardId: string
  name: string
  alternativeNames?: string[]
  address: string
  lat: number
  lng: number
  mapStatus: MapStatus
  cardVersion?: string
  cardStatus?: string
  style: string
  yearBuilt: string
  headline: string
  methodologyNote: string
  architect?: string
  protectionStatus?: string
  summary: string
  verification?: BuildingVerification
  memoryTraces: MemoryTrace[]
  artifacts: Artifact[]
  timeline: TimelineStage[]
  photos: PhotoRef[]
  hotspots: Hotspot[]
  sources: { id: string; name: string; url?: string }[]
}

export interface TourStop {
  buildingId: string
  title: string
  methodologyNote: string
}
