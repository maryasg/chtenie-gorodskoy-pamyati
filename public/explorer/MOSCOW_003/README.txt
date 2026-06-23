Сюда попадают экспорты Archiview для здания MOSCOW_003 (Чистопрудный).

Нужные файлы (скопируйте из папки result проекта Archiview):
  03_historical_rectified.png  →  historical-rectified.png  (ползунок до/после на сайте)
  04_modern_rectified.png      →  modern-rectified.png
  06_marked_rectified.png      →  marked-facade.png  (overlay; координаты polygon совпадают)
  11_modern_source_for_site.png  →  modern-source.png  (карточка здания)
  20260520_185142.jpg          →  20260520_185142.jpg  (AR-preview)
  07_marked_on_original_modern.png  →  архив/проверка, не основной файл сайта для overlay
  08_marked_on_original_modern_labeled.png  →  marked-facade-labeled.png  (по желанию)
  annotations/manual_annotations.json  →  annotations.json
  project_v8.json  →  facade-project.json (через copy_to_website.bat)
    — H_rect_to_modern для modern-source; при другом кадре AR-фото добавьте H_rect_to_ar

После копирования: GitHub Desktop → Commit → Push.

Или запустите в папке Archiview v15: copy_to_website.bat
