# Быстрый старт (Windows)

## 1. Куда вставить ключ

Файл **`.env`** в корне проекта:

```
C:\Users\Marusia\Projects\articles_KorolevSP\.env
```

Создать из шаблона:

```bat
cd C:\Users\Marusia\Projects\articles_KorolevSP
copy .env.example .env
notepad .env
```

Минимум для теста **только текстов** (KupiAPI):

```env
OPENAI_API_KEY=rk_live_ваш-ключ
OPENAI_BASE_URL=https://kupiapi.ru/v1
TEXT_MODEL=gpt-4o-mini
```

Ключ вставляется **в `.env`**, не в папку `.venv`.

---

## 2. Куда класть темы

Все ваши темы уже разложены по месяцам в папке **`content_plan/`**:

```
content_plan/
  ноябрь.json    ← 15 тем (написаны)
  декабрь.json   ← 16 тем
  январь.json    ← 15 тем
  февраль.json   ← 15 тем
  март.json      ← 15 тем
  май.json       ← 15 тем (план)
  июнь.json      ← 15 тем (план)
  июль.json      ← 15 тем (план)
  all.json       ← все 121 тема
```

Файл **`content_plan.json`** в корне = копия **`май.json`** (текущий план по умолчанию).

### Запуск по месяцам

```bat
python generate.py --plan content_plan\май.json --skip-images
python generate.py --plan content_plan\июнь.json --number 03 --skip-images
python generate.py --plan content_plan\all.json --filter-month май --skip-images
```

### Добавить новую тему вручную

Откройте нужный месяц, например `content_plan\май.json`:

```json
{
  "month": "май",
  "number": "16",
  "title": "Новая тема: заголовок статьи"
}
```

Или пересоберите планы из `build_content_plan.py` (если правили скрипт).

### Вариант A — файл плана (много тем)

`content_plan.json` в корне проекта (по умолчанию — май):

```json
[
  {
    "month": "май",
    "number": "01",
    "title": "Кровоточивость дёсен: когда это уже заболевание"
  }
]
```

Запуск всех тем:

```bat
python generate.py
```

Одна тема из плана:

```bat
python generate.py --number 02
```

### Вариант B — любая тема без правки JSON

```bat
python generate.py --title "Кровоточивость дёсен: когда это уже заболевание" --skip-images
```

С номером и месяцем:

```bat
python generate.py --title "Отбеливание зубов: мифы и факты" --month июнь --number 07 --skip-images
```

---

## 3. Как общаться с генератором

**Интерфейса нет** — только **окно cmd** (чёрное окно команд).

Вы пишете команды → скрипт генерирует → результат в папке `output\`.

Это не чат. Чтобы «попросить тему», используйте `--title` или добавьте строку в `content_plan.json`.

---

## 4. Первая пробная статья

```bat
cd C:\Users\Marusia\Projects\articles_KorolevSP
.venv\Scripts\activate
python generate.py --title "Кровоточивость дёсен: когда это уже заболевание" --skip-images
```

Результат:

```
output\май\99-krovotochivost-desen\
  vk.md
  telegram.md
  image_prompt.txt
  meta.json
```

Откройте `vk.md` и `telegram.md` в Блокноте.

---

## 5. Картинка (когда настроите IMAGE_API_KEY)

```bat
python generate.py --images-only --number 99
```

Или сразу с текстом:

```bat
python generate.py --title "Кровоточивость дёсен: когда это уже заболевание"
```
