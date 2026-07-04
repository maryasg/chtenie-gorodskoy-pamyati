import { Link } from 'react-router-dom'

export function HomeV2() {
  return (
    <div className="space-y-6">
      <section className="v2-card p-6 sm:p-8">
        <p className="v2-kicker">Ветка cursor/lovable-design-v2-3b69</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
          Здесь будет новый дизайн
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-v2-muted sm:text-base">
          Это отдельная версия сайта по адресу <code className="text-v2-ink">/v2/</code>. Текущий
          боевой сайт на главной не меняется, пока вы не решите слить ветку в{' '}
          <code className="text-v2-ink">main</code>.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            to="/v2/map"
            className="inline-flex rounded-full bg-v2-accent px-4 py-2 text-sm font-medium text-white transition hover:opacity-90"
          >
            Карта (черновик)
          </Link>
          <Link
            to="/"
            className="inline-flex rounded-full border border-v2-line px-4 py-2 text-sm font-medium text-v2-ink transition hover:bg-v2-surface-muted"
          >
            Сравнить с текущим сайтом
          </Link>
        </div>
      </section>

      <section className="v2-card border-dashed p-6 text-sm text-v2-muted">
        <p className="font-medium text-v2-ink">Следующий шаг</p>
        <p className="mt-2">
          Пришлите публичную ссылку Share preview из Lovable или скриншоты — перенесём стилистику
          сюда: типографика, цвета, сетка, навигация.
        </p>
      </section>
    </div>
  )
}
