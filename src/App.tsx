import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ARPage } from './pages/ARPage'
import { BuildingPage } from './pages/BuildingPage'
import { ExplorerPage } from './pages/ExplorerPage'
import { MapPage } from './pages/MapPage'
import { TourPage } from './pages/TourPage'

export default function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, '') || '/'}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<MapPage />} />
          <Route path="tour" element={<TourPage />} />
          <Route path="explorer" element={<ExplorerPage />} />
          <Route path="building/:id" element={<BuildingPage />} />
          <Route path="building/:id/ar" element={<ARPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
