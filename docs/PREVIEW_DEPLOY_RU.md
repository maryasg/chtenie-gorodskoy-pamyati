# Preview-деплой веток и Pull Request'ов

Preview-деплой нужен, чтобы посмотреть изменения на сайте **до слияния с `main`**.

Общий статус проекта и очередь задач: [`ПРОДОЛЖИТЬ_РАБОТУ.md`](../ПРОДОЛЖИТЬ_РАБОТУ.md).

## Где будет ссылка

После пуша в ветку `cursor/...` или обновления Pull Request'а запускается GitHub Actions workflow:

```txt
Build preview source
```

После его успешного завершения автоматически запускается второй workflow:

```txt
Deploy preview to GitHub Pages
```

Ссылка появится:

1. в GitHub Actions у завершённого workflow;
2. в карточке deployment/environment `github-pages`;
3. по предсказуемому адресу ниже.

## Ссылка для Pull Request

Для PR номер `4`:

```txt
https://maryasg.github.io/chtenie-gorodskoy-pamyati/pr-preview/pr-4/
```

Общий шаблон:

```txt
https://maryasg.github.io/chtenie-gorodskoy-pamyati/pr-preview/pr-НОМЕР_PR/
```

## Ссылка для ветки

Для ветки:

```txt
cursor/curator-hotspot-cards-a0b3
```

preview будет здесь:

```txt
https://maryasg.github.io/chtenie-gorodskoy-pamyati/branch-preview/cursor-curator-hotspot-cards-a0b3/
```

Общий шаблон:

```txt
https://maryasg.github.io/chtenie-gorodskoy-pamyati/branch-preview/ИМЯ-ВЕТКИ-С-ДЕФИСАМИ/
```

Слеши в имени ветки заменяются на дефисы.

## Как это работает технически

Preview работает в два шага:

1. `Build preview source` запускается на Pull Request или ветку `cursor/...` и проверяет, что ветка собирается.
2. `Deploy preview to GitHub Pages` запускается из `main`, забирает нужную ветку и публикует preview.

Второй workflow собирает два варианта сайта:

1. текущий `main` кладётся в корень GitHub Pages, чтобы основной сайт не заменялся содержимым ветки;
2. preview-ветка или PR кладётся в отдельную подпапку:
   - `pr-preview/pr-N/` для Pull Request;
   - `branch-preview/name-of-branch/` для ветки.

## Важное ограничение

Preview-деплой использует тот же GitHub Pages сайт, что и основной сайт. Поэтому последний деплой GitHub Pages публикует полный набор файлов заново:

- основной сайт в корне берётся из `main`;
- preview кладётся в отдельную подпапку.

Если основной deploy из `main` запустится позже, preview-папка может временно исчезнуть. Чтобы вернуть preview, достаточно ещё раз запушить ветку или закрыть/открыть Pull Request.

## Как запустить preview вручную

Если автоматический запуск не сработал или нужно пересобрать preview:

1. Откройте GitHub → **Actions**.
2. Выберите workflow **Deploy preview to GitHub Pages**.
3. Нажмите **Run workflow**.
4. В выпадающем списке ветки выберите `main`.
5. В поле `preview_ref` укажите ветку, например:

   ```txt
   cursor/curator-hotspot-cards-a0b3
   ```

6. Если нужна ссылка вида `/pr-preview/pr-4/`, в поле `pr_number` укажите:

   ```txt
   4
   ```

7. Запустите workflow и дождитесь зелёной галочки.

## Для прямых ссылок внутри preview

Открывать лучше корневую preview-ссылку, например:

```txt
https://maryasg.github.io/chtenie-gorodskoy-pamyati/pr-preview/pr-4/
```

А дальше переходить по сайту кликами. Прямое обновление глубокой ссылки вроде `/building/...` может зависеть от fallback GitHub Pages.
