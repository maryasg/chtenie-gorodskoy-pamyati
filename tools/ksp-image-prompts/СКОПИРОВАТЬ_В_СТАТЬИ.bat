@echo off
chcp 65001 >nul
set SRC=%~dp0
set DST=%USERPROFILE%\Projects\maryasg-articles_KorolevSP

if not exist "%DST%" (
    echo Папка не найдена: %DST%
    echo Сначала клонируйте репозиторий статей.
    pause
    exit /b 1
)

echo Копирую скрипты в %DST%
copy /Y "%SRC%build_image_prompts.py" "%DST%\"
copy /Y "%SRC%build_image_prompts.bat" "%DST%\"
copy /Y "%SRC%docx_export.py" "%DST%\"
copy /Y "%SRC%export_docx.py" "%DST%\"
copy /Y "%SRC%export_docx.bat" "%DST%\"
copy /Y "%SRC%pack_month.py" "%DST%\"
copy /Y "%SRC%pack_month.bat" "%DST%\"
copy /Y "%SRC%СОБРАТЬ_ПЛОСКИЕ_ФАЙЛЫ.bat" "%DST%\"
copy /Y "%SRC%generate.py" "%DST%\"
copy /Y "%SRC%test_kupiapi.py" "%DST%\"
copy /Y "%SRC%test_kupiapi.bat" "%DST%\"
copy /Y "%SRC%requirements.txt" "%DST%\"
copy /Y "%SRC%ИНСТРУКЦИЯ.md" "%DST%\"
copy /Y "%SRC%ИНСТРУКЦИЯ_ДЛЯ_ПЕЧАТИ.md" "%DST%\"
copy /Y "%SRC%prompts\cover_template_title.txt" "%DST%\prompts\"

echo.
echo Обновите зависимости (один раз после копирования):
echo   cd /d "%DST%"
echo   .venv\Scripts\activate
echo   pip install -r requirements.txt
echo.
echo Готово. Собираю 121 промпт...
cd /d "%DST%"
call build_image_prompts.bat --force

echo.
echo Для проверки KupiAPI:
echo   test_kupiapi.bat
echo.
echo Для плоских файлов за месяц запустите:
echo   СОБРАТЬ_ПЛОСКИЕ_ФАЙЛЫ.bat июнь
echo.
echo Инструкция для печати:
echo   %DST%\ИНСТРУКЦИЯ_ДЛЯ_ПЕЧАТИ.md
echo.
echo Промпты в папке: %DST%\image_prompts\
pause
