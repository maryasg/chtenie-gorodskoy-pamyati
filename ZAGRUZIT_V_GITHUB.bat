@echo off
chcp 65001 >nul
echo ============================================
echo   Загрузка генератора в articles_KorolevSP
echo ============================================
echo.

set TARGET=%USERPROFILE%\Projects\articles_KorolevSP

if exist "%TARGET%" (
    echo Папка уже есть, переименую в articles_KorolevSP-old...
    if exist "%TARGET%-old" rmdir /S /Q "%TARGET%-old"
    move "%TARGET%" "%TARGET%-old"
)

echo [1/3] Скачиваю готовый проект...
git clone --branch articles_KorolevSP --single-branch https://github.com/maryasg/chtenie-gorodskoy-pamyati.git "%TARGET%"
if errorlevel 1 goto error

echo.
echo [2/3] Подключаю ваш репозиторий GitHub...
cd /d "%TARGET%"
git remote set-url origin https://github.com/maryasg/articles_KorolevSP.git

echo.
echo [3/3] Отправляю файлы на GitHub...
git push -u origin articles_KorolevSP:main --force
if errorlevel 1 goto error

echo.
echo ============================================
echo   ГОТОВО!
echo   Папка: %TARGET%
echo.
echo   Следующие шаги:
echo   cd %TARGET%
echo   python -m venv .venv
echo   .venv\Scripts\activate
echo   pip install -r requirements.txt
echo   copy .env.example .env
echo   notepad .env
echo ============================================
pause
exit /b 0

:error
echo.
echo Что-то пошло не так. Но папка могла скачаться: %TARGET%
echo Проверьте: установлен ли git, есть ли репозиторий на GitHub,
echo и вошли ли вы в GitHub при запросе логина.
pause
exit /b 1
