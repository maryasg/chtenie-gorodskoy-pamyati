# KSP Content Generator

Автоматическая генерация статей для ВКонтакте и Telegram и обложек 16:9 для **Королёвской стоматологической поликлиники**.

Проект **полностью отдельный** от сайта «Память стен» и Archiview. Работает локально на вашем компьютере.

## Куда положить на Windows

```
C:\Users\Marusia\Projects\ksp-content-generator
```

## Что делает скрипт

По каждой теме из `content_plan.json`:

1. Пишет статью для ВКонтакте (`vk.md`)
2. Пишет сокращённую версию для Telegram (`telegram.md`)
3. Формирует промпт для обложки (`image_prompt.txt`)
4. Генерирует обложку 16:9 (`cover.png`) через OpenAI Image API
5. Сохраняет служебные данные (`meta.json`)

Результат:

```
output/
  май/
    02-nepravilnaya-chistka-zubov/
      vk.md
      telegram.md
      image_prompt.txt
      cover.png
      meta.json
```

## Требования

- Python **3.10–3.13**
- Ключ OpenAI API: https://platform.openai.com/api-keys
- Интернет

## Установка (Windows, cmd)

```bat
cd C:\Users\Marusia\Projects\ksp-content-generator

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

copy .env.example .env
```

Откройте `.env` в блокноте и вставьте ключ:

```
OPENAI_API_KEY=sk-ваш-ключ
```

## Запуск

Все темы из плана:

```bat
python generate.py
```

Одна тема:

```bat
python generate.py --number 04
```

Только тексты, без картинок (если хотите сначала проверить статьи):

```bat
python generate.py --skip-images
```

Перегенерировать заново:

```bat
python generate.py --force
```

## Настройки в `.env`

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `OPENAI_API_KEY` | — | Ключ API |
| `TEXT_MODEL` | `gpt-4o` | Модель для статей |
| `IMAGE_MODEL` | `dall-e-3` | Модель для обложек |
| `IMAGE_SIZE` | `1792x1024` | Формат 16:9 для dall-e-3 |

## Формат content_plan.json

```json
[
  {
    "month": "май",
    "number": "01",
    "title": "Кровоточивость дёсен: когда это уже заболевание"
  }
]
```

Добавляйте новые темы в этот файл и снова запускайте `python generate.py`.

## Проверка качества

После генерации скрипт проверяет:

- есть ли обе версии статьи;
- объём VK (2500–3000) и Telegram (1200–1500);
- телефон и ссылка на запись;
- хэштеги одной строкой;
- нет подозрительных фраз (лекарства, гарантии, лишние ссылки);
- в промпт обложки подставлен текст Telegram.

Замечания пишутся в консоль и в `meta.json` → `validation_issues`.

Код выхода `2` означает, что есть замечания — просмотрите тексты и при необходимости перегенерируйте с `--force`.

## Промпты

Шаблоны лежат в `prompts/`:

- `vk_system.txt` — стиль статей для ВК
- `telegram_system.txt` — сокращённая версия
- `cover_template.txt` — шаблон промпта для обложки

Можно править вручную под ваш тон.

## Стоимость API

Списание идёт с баланса OpenAI Platform (не с подписки ChatGPT Plus). Ориентировочно: одна тема = 2 запроса текста + 1 картинка.

## Безопасность

- Не коммитьте `.env` и не выкладывайте ключ.
- Папка `output/` в `.gitignore` — готовые материалы остаются локально.

## Проблемы

**«OPENAI_API_KEY не задан»** — создайте `.env` из `.env.example`.

**Объём статьи не в диапазоне** — перезапустите с `--force` или подправьте текст вручную.

**Картинка не нравится** — удалите `cover.png` и запустите снова только для этой темы: `python generate.py --number 04 --force`.
