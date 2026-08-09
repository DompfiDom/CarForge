@echo off
setlocal EnableExtensions EnableDelayedExpansion

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo Fehler: Das Skript muss im Git-Repository ausgefuehrt werden.
    exit /b 1
)

git add -A
if errorlevel 1 (
    echo Fehler: Aenderungen konnten nicht vorgemerkt werden.
    exit /b 1
)

git diff --cached --quiet
if not errorlevel 1 (
    echo Keine Aenderungen zum Committen gefunden.
    exit /b 1
)

if not exist .version (
    echo Fehler: Die Datei .version fehlt.
    exit /b 1
)

set /p CURRENT_VERSION=<.version
for /f "tokens=1-3 delims=." %%A in ("!CURRENT_VERSION!") do (
    set "VERSION_MAJOR=%%A"
    set "VERSION_MINOR=%%B"
    set "VERSION_BUILD=%%C"
)

echo(!VERSION_BUILD!| findstr /r "^[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo Fehler: Ungueltige Version in .version: !CURRENT_VERSION!
    exit /b 1
)

set /a VERSION_BUILD+=1
set "NEXT_VERSION=!VERSION_MAJOR!.!VERSION_MINOR!.!VERSION_BUILD!"
> .version echo !NEXT_VERSION!
git add -- .version

set "COMMIT_MESSAGE=%~1"
if not defined COMMIT_MESSAGE set "COMMIT_MESSAGE=chore: release !NEXT_VERSION!"

git commit -m "!COMMIT_MESSAGE!"
if errorlevel 1 (
    echo Fehler: Commit fehlgeschlagen. .version ist bereits auf !NEXT_VERSION! gesetzt.
    exit /b 1
)

git push
if errorlevel 1 (
    echo Fehler: Push fehlgeschlagen. Der Commit existiert weiterhin lokal.
    exit /b 1
)

echo Erfolgreich veroeffentlicht: Version !NEXT_VERSION!
