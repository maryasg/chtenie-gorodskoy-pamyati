import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ScrollToTop } from './components/ScrollToTop'
import { ARPage } from './pages/ARPage'
import { BuildingPage } from './pages/BuildingPage'
import { ExpertReviewPage } from './pages/ExpertReviewPage'
import { ExplorerPage } from './pages/ExplorerPage'
import { MapPage } from './pages/MapPage'
import { MethodPage } from './pages/MethodPage'
import { TourPage } from './pages/TourPage'
import { LayoutV2 } from './v2/LayoutV2'
import { HomeV2 } from './v2/pages/HomeV2'
import { MapPageV2 } from './v2/pages/MapPageV2'
import { BuildingPageV2 } from './v2/pages/BuildingPageV2'

function LegacyCuratorRedirect() {
  const { id } = useParams<{ id: string }>()
  return <Navigate to={id ? `/expert/${id}` : '/'} replace />
}

export default function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, '') || '/'}>
      <ScrollToTop />
      <Routes>
        <Route path="v2" element={<LayoutV2 />}>
          <Route index element={<HomeV2 />} />
          <Route path="map" element={<MapPageV2 />} />
          <Route path="building/:id" element={<BuildingPageV2 />} />
        </Route>
        <Route element={<Layout />}>
          <Route index element={<MapPage />} />
          <Route path="method" element={<MethodPage />} />
          <Route path="tour" element={<TourPage />} />
          <Route path="explorer" element={<ExplorerPage />} />
          <Route path="building/:id" element={<BuildingPage />} />
          <Route path="building/:id/ar" element={<ARPage />} />
          <Route path="expert/:id" element={<ExpertReviewPage />} />
          <Route path="curator/:id" element={<LegacyCuratorRedirect />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
