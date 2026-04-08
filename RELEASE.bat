@echo off
chcp 65001 >nul
title EITO LABS - Release Tool

echo ============================================
echo   MARKETPLACE REPOSTER PRO - RELEASE TOOL
echo ============================================
echo.

REM Ler versao atual do paths.py
for /f "tokens=2 delims==" %%a in ('findstr "APP_VERSION" gui\utils\paths.py') do (
    set CURRENT_VERSION=%%~a
)
set CURRENT_VERSION=%CURRENT_VERSION: =%
set CURRENT_VERSION=%CURRENT_VERSION:"=%

echo Versao atual: v%CURRENT_VERSION%
echo.

REM Pedir nova versao
set /p NEW_VERSION="Nova versao (ex: 3.1.0): "
if "%NEW_VERSION%"=="" (
    echo Versao nao informada. Abortando.
    pause
    exit /b 1
)

REM Pedir notas da versao
set /p RELEASE_NOTES="Notas da versao (opcional): "

echo.
echo ============================================
echo  Etapa 1/4: Atualizando versao no codigo...
echo ============================================

REM Atualizar APP_VERSION em paths.py
powershell -Command "(Get-Content 'gui\utils\paths.py') -replace 'APP_VERSION = \".*\"', 'APP_VERSION = \"%NEW_VERSION%\"' | Set-Content 'gui\utils\paths.py'"

REM Atualizar installer.iss
powershell -Command "(Get-Content 'installer.iss') -replace '#define MyAppVersion \".*\"', '#define MyAppVersion \"%NEW_VERSION%\"' | Set-Content 'installer.iss'"

echo Versao atualizada para v%NEW_VERSION%

echo.
echo ============================================
echo  Etapa 2/4: Buildando o executavel...
echo ============================================

call BUILD.bat
if errorlevel 1 (
    echo ERRO no build! Abortando.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Etapa 3/4: Criando Release no GitHub...
echo ============================================

REM Commitar as mudancas de versao
git add gui\utils\paths.py installer.iss version.json
git commit -m "release: v%NEW_VERSION%"
git push origin master

REM Criar release no GitHub com o installer
set INSTALLER_PATH=installer_output\MarketplaceReposterPro_Setup_v%NEW_VERSION%.exe
if exist "%INSTALLER_PATH%" (
    gh release create "v%NEW_VERSION%" "%INSTALLER_PATH%" --title "v%NEW_VERSION%" --notes "%RELEASE_NOTES%" --latest
) else (
    echo Installer nao encontrado em %INSTALLER_PATH%
    echo Criando release sem arquivo...
    gh release create "v%NEW_VERSION%" --title "v%NEW_VERSION%" --notes "%RELEASE_NOTES%" --latest
)

REM Pegar URL de download do release
for /f "delims=" %%u in ('gh release view "v%NEW_VERSION%" --json assets --jq ".assets[0].url" 2^>nul') do set DOWNLOAD_URL=%%u
if "%DOWNLOAD_URL%"=="" (
    for /f "delims=" %%u in ('gh release view "v%NEW_VERSION%" --json url --jq ".url" 2^>nul') do set DOWNLOAD_URL=%%u
)

echo.
echo ============================================
echo  Etapa 4/4: Atualizando Gist de versao...
echo ============================================

REM Atualizar version.json local
powershell -Command "$json = @{version='%NEW_VERSION%'; download_url='%DOWNLOAD_URL%'; notes='%RELEASE_NOTES%'} | ConvertTo-Json; $json | Set-Content 'version.json' -Encoding UTF8"

REM Atualizar o Gist remoto
gh gist edit 4d60d5d8fb0d3322974ff46b812112a5 version.json

echo.
echo ============================================
echo  RELEASE v%NEW_VERSION% CONCLUIDA!
echo ============================================
echo.
echo O que aconteceu:
echo   1. Versao atualizada no codigo
echo   2. Executavel buildado
echo   3. Release criado no GitHub
echo   4. Gist de versao atualizado
echo.
echo Agora quando o cliente abrir o app, vai ver
echo a notificacao de atualizacao automaticamente!
echo.
pause
