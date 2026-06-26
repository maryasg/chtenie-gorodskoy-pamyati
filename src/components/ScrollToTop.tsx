import { useLayoutEffect } from 'react'
import { useLocation } from 'react-router-dom'

/** При смене маршрута — показывать страницу с начала, не с сохранённой позиции прокрутки. */
export function ScrollToTop() {
  const { pathname, hash } = useLocation()

  useLayoutEffect(() => {
    if (hash) return
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' })
  }, [pathname, hash])

  return null
}
