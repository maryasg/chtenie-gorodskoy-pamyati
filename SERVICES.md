# Каталог моделей и сервисов

Генератор использует **OpenAI-совместимый API**. Подходит любой сервис с форматом `/v1/chat/completions` и `/v1/images/generations`.

## Ваш провайдер: KupiAPI

| Параметр | Значение |
|----------|----------|
| Base URL | `https://kupiapi.ru/v1` |
| Ключ | ваш API-ключ от KupiAPI |
| Формат | OpenAI-compatible |

В `.env`:

```env
OPENAI_API_KEY=ваш-ключ-kupiapi
OPENAI_BASE_URL=https://kupiapi.ru/v1
```

---

## Модели для ТЕКСТОВ (статьи VK + Telegram)

Цены: Input — токены запроса, Output — токены ответа (Output обычно в 3–5 раз дороже).

### Рекомендация для вашей задачи

| Задача | Модель | ID | Почему |
|--------|--------|-----|--------|
| **Основная (много тем)** | GPT-4o Mini | `gpt-4o-mini` | Лучший баланс цена/качество, хороший русский, соблюдает структуру |
| **Черновик / массовая генерация** | DeepSeek V3 | `deepseek-chat` | Самый дешёвый нормальный вариант |
| **Если mini «плывёт» по стилю** | GPT-4o | `gpt-4o` | Стабильнее по тону и медицинским формулировкам |
| **Премиум-качество** | Claude Sonnet | `claude-sonnet` | Отличный русский и спокойный тон, но дороже |
| **Быстрые правки** | Claude Haiku | `claude-haiku` | Дешевле Sonnet, для коротких доработок |

### Не рекомендую для статей

| Модель | ID | Почему нет |
|--------|-----|------------|
| DeepSeek R1 | `deepseek-reasoner` | Модель «рассуждений», медленнее и дороже — для копирайта не нужна |
| GPT-5.5 | `gpt-5.5` | Избыточно дорого для типовых постов |
| Claude Opus | `claude-opus` | Максимальная цена, для VK/Telegram нет смысла |
| GPT-5.4 Nano | `gpt-5.4-nano` | Слишком слабая для длинных медицинских текстов с проверками |
| GPT-5.4 | `gpt-5.4` | Дорого без явного выигрыша над gpt-4o |

### Сравнение по стоимости (пример на 1 тему)

Одна тема = 2 запроса (VK ~2800 символов + Telegram ~1400 символов).

Ориентировочно ~2 500 input-токенов и ~2 000 output-токенов на тему:

| Модель | ≈ цена за 1 тему | ≈ цена за 30 тем/мес |
|--------|------------------|----------------------|
| `deepseek-chat` | ~0,05 ₽ | ~1,5 ₽ |
| `gpt-4o-mini` | ~0,04 ₽ | ~1,2 ₽ |
| `gpt-5.4-mini` | ~0,16 ₽ | ~5 ₽ |
| `gpt-4o` | ~0,5 ₽ | ~15 ₽ |
| `claude-haiku` | ~0,25 ₽ | ~7,5 ₽ |
| `claude-sonnet` | ~0,75 ₽ | ~22 ₽ |
| `claude-opus` | ~3,5 ₽ | ~105 ₽ |

*Оценка приблизительная; реальная цена зависит от длины промптов.*

---

## Модели для КАРТИНОК (обложки 16:9)

### Важно: KupiAPI — только тексты

**KupiAPI не генерирует картинки.** Там есть только `/v1/chat/completions` (GPT, Claude, DeepSeek).

Для обложек нужен **второй сервис** с Image API.

### Рекомендуемая схема

| Что | Сервис | Переменные в `.env` |
|-----|--------|---------------------|
| Тексты | KupiAPI | `OPENAI_API_KEY`, `OPENAI_BASE_URL` |
| Картинки | ProxyAPI или OpenAI | `IMAGE_API_KEY`, `IMAGE_BASE_URL` |

### Вариант 1 — ProxyAPI (удобно из России)

Сайт: https://proxyapi.ru  
Документация по картинкам: https://proxyapi.ru/docs/openai-image-generation

```env
# Тексты
OPENAI_API_KEY=rk_live_...
OPENAI_BASE_URL=https://kupiapi.ru/v1
TEXT_MODEL=gpt-4o-mini

# Картинки
IMAGE_API_KEY=ваш-ключ-proxyapi
IMAGE_BASE_URL=https://api.proxyapi.ru/openai/v1
IMAGE_MODEL=dall-e-3
IMAGE_SIZE=1792x1024
```

### Вариант 2 — OpenAI напрямую (только картинки)

```env
OPENAI_API_KEY=rk_live_...
OPENAI_BASE_URL=https://kupiapi.ru/v1
TEXT_MODEL=gpt-4o-mini

IMAGE_API_KEY=sk-ваш-ключ-openai
IMAGE_BASE_URL=https://api.openai.com/v1
IMAGE_MODEL=dall-e-3
IMAGE_SIZE=1792x1024
```

### Какие image-модели брать

| Модель | ID | Когда |
|--------|-----|-------|
| **DALL·E 3** | `dall-e-3` | ✅ лучший выбор: 16:9, русский текст на обложке |
| GPT Image | `gpt-image-1` | альтернатива, если есть у провайдера |
| GPT Image 2 | `gpt-image-2` | новее, у ProxyAPI |

Размер для 16:9: **`1792x1024`**

### Как запускать картинки

Всё сразу (тексты + обложка):

```bat
python generate.py --number 02
```

Сначала тексты, потом обложки:

```bat
python generate.py --skip-images
python generate.py --images-only
```

Одна обложка заново:

```bat
python generate.py --images-only --number 04 --force
```

Готовые файлы: `output\май\02-...\cover.png`

---

## Готовые профили для `.env`

### Профиль «Эконом» (много тем, минимум затрат)

```env
OPENAI_API_KEY=ваш-ключ
OPENAI_BASE_URL=https://kupiapi.ru/v1
TEXT_MODEL=deepseek-chat
IMAGE_MODEL=dall-e-3
IMAGE_SIZE=1792x1024
```

### Профиль «Баланс» — рекомендуемый

```env
OPENAI_API_KEY=ваш-ключ
OPENAI_BASE_URL=https://kupiapi.ru/v1
TEXT_MODEL=gpt-4o-mini
IMAGE_MODEL=dall-e-3
IMAGE_SIZE=1792x1024
```

### Профиль «Качество»

```env
OPENAI_API_KEY=ваш-ключ
OPENAI_BASE_URL=https://kupiapi.ru/v1
TEXT_MODEL=gpt-4o
IMAGE_MODEL=dall-e-3
IMAGE_SIZE=1792x1024
```

### Профиль «Премиум-текст»

```env
OPENAI_API_KEY=ваш-ключ
OPENAI_BASE_URL=https://kupiapi.ru/v1
TEXT_MODEL=claude-sonnet
IMAGE_MODEL=dall-e-3
IMAGE_SIZE=1792x1024
```

### Только тексты (без оплаты картинок)

```env
OPENAI_API_KEY=ваш-ключ
OPENAI_BASE_URL=https://kupiapi.ru/v1
TEXT_MODEL=gpt-4o-mini
```

Запуск: `python generate.py --skip-images`

---

## Полный каталог моделей KupiAPI (текст)

### OpenAI / GPT

| Модель | ID | Input ₽/1M | Output ₽/1M | Для текстов |
|--------|-----|------------|-------------|-------------|
| GPT-5.4 Nano | `gpt-5.4-nano` | 3 | 12 | ⚠️ только тесты |
| GPT-5.4 Mini | `gpt-5.4-mini` | 15 | 60 | ✅ средний вариант |
| GPT-5.4 | `gpt-5.4` | 100 | 300 | ⚠️ дорого |
| GPT-5.5 | `gpt-5.5` | 200 | 600 | ❌ избыточно |
| GPT-4o Mini | `gpt-4o-mini` | 4 | 16 | ✅ **рекомендуем** |
| GPT-4o | `gpt-4o` | 50 | 200 | ✅ если нужно качество |

### Anthropic / Claude

| Модель | ID | Input ₽/1M | Output ₽/1M | Для текстов |
|--------|-----|------------|-------------|-------------|
| Claude Haiku | `claude-haiku` | 20 | 100 | ✅ правки, короткие задачи |
| Claude Sonnet | `claude-sonnet` | 60 | 300 | ✅ премиум-тексты |
| Claude Opus | `claude-opus` | 300 | 1500 | ❌ слишком дорого |

### DeepSeek

| Модель | ID | Input ₽/1M | Output ₽/1M | Для текстов |
|--------|-----|------------|-------------|-------------|
| DeepSeek V3 | `deepseek-chat` | 5 | 20 | ✅ самый дешёвый |
| DeepSeek R1 | `deepseek-reasoner` | 10 | 40 | ❌ не для статей |

---

## Другие сервисы (если понадобятся позже)

| Сервис | Base URL | Ключ в `.env` | Тексты | Картинки |
|--------|----------|---------------|--------|----------|
| **KupiAPI** | `https://kupiapi.ru/v1` | `OPENAI_API_KEY` | ✅ | ✅* |
| OpenAI напрямую | `https://api.openai.com/v1` | `OPENAI_API_KEY` | ✅ | ✅ |
| OpenRouter | `https://openrouter.ai/api/v1` | `OPENAI_API_KEY` | ✅ | ⚠️ |
| Together AI | `https://api.together.xyz/v1` | `OPENAI_API_KEY` | ✅ | ⚠️ |
| YandexGPT | свой API | отдельная доработка | ✅ | ⚠️ |
| GigaChat | свой API | отдельная доработка | ✅ | ❌ |

\* если image-модели включены в вашем тарифе KupiAPI

---

## Итог: что поставить вам

```env
OPENAI_API_KEY=ваш-ключ-kupiapi
OPENAI_BASE_URL=https://kupiapi.ru/v1
TEXT_MODEL=gpt-4o-mini
IMAGE_MODEL=dall-e-3
IMAGE_SIZE=1792x1024
```

- **Тексты:** `gpt-4o-mini` (или `deepseek-chat` если ещё дешевле нужно)
- **Картинки:** `dall-e-3` — уточните наличие и цену в KupiAPI
