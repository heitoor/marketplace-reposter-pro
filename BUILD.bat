@echo off
chcp 65001 >nul 2>&1
title EITO LABS - Build do Instalador
echo.
echo =============================================
echo   EITO LABS - Build do Instalador
echo   Marketplace Reposter Pro
echo =============================================
echo.

REM --- Verifica Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale o Python 3.10+ primeiro.
    pause
    exit /b 1
)

REM --- Instala dependencias do projeto (inclui PyInstaller) ---
echo.
echo [1/3] Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)
echo       OK

REM --- Limpa builds anteriores ---
echo.
echo [2/3] Gerando executavel com PyInstaller...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM --- Roda PyInstaller ---
python -m PyInstaller reposter.spec --noconfirm
if errorlevel 1 (
    echo.
    echo [ERRO] PyInstaller falhou. Verifique os erros acima.
    pause
    exit /b 1
)
echo       OK

REM --- Verifica se o .exe foi gerado ---
if not exist "dist\MarketplaceReposterPro\MarketplaceReposterPro.exe" (
    echo [ERRO] Executavel nao foi gerado.
    pause
    exit /b 1
)

REM --- Verifica Inno Setup ---
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
)
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
)

if defined ISCC (
    echo.
    echo [3/3] Gerando instalador com Inno Setup...
    "%ISCC%" installer.iss
    if errorlevel 1 (
        echo [ERRO] Inno Setup falhou.
        pause
        exit /b 1
    )
    echo       OK
    echo.
    echo =============================================
    echo   BUILD COMPLETO!
    echo.
    echo   Instalador gerado em:
    echo   installer_output\MarketplaceReposterPro_Setup_v1.0.0.exe
    echo =============================================
) else (
    echo.
    echo [AVISO] Inno Setup 6 nao encontrado.
    echo         Baixe em: https://jrsoftware.org/isdl.php
    echo.
    echo         O executavel portavel esta disponivel em:
    echo         dist\MarketplaceReposterPro\MarketplaceReposterPro.exe
    echo.
    echo         Voce pode zipar a pasta dist\MarketplaceReposterPro\
    echo         e enviar ao cliente como alternativa.
    echo =============================================
)

echo.
pause
