@echo off
title Instalador Automatico - Marketplace Reposter
color 0A

cls
echo.
echo ===================================================================
echo.
echo      INSTALADOR AUTOMATICO - MARKETPLACE REPOSTER
echo                     Versao 2.0
echo.
echo ===================================================================
echo.
echo Este instalador vai:
echo   - Verificar Python
echo   - Instalar dependencias
echo   - Configurar ChromeDriver
echo   - Criar estrutura de pastas
echo.
echo Pressione qualquer tecla para comecar...
pause >nul

:: ============================================
:: ETAPA 1: VERIFICAR PYTHON
:: ============================================
cls
echo.
echo ===================================================================
echo  ETAPA 1/5: Verificando Python...
echo ===================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Por favor, instale o Python primeiro:
    echo   1. Acesse: https://www.python.org/downloads/
    echo   2. Baixe a versao mais recente
    echo   3. Durante instalacao, MARQUE: "Add Python to PATH"
    echo   4. Rode este instalador novamente
    echo.
    echo Abrindo pagina de download...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python encontrado: %PYTHON_VERSION%
timeout /t 2 >nul

:: ============================================
:: ETAPA 2: VERIFICAR PIP
:: ============================================
cls
echo.
echo ===================================================================
echo  ETAPA 2/5: Verificando pip...
echo ===================================================================
echo.

python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [AVISO] pip nao encontrado. Instalando...
    python -m ensurepip --default-pip
    python -m pip install --upgrade pip
)

echo [OK] pip verificado
timeout /t 2 >nul

:: ============================================
:: ETAPA 3: INSTALAR DEPENDENCIAS
:: ============================================
cls
echo.
echo ===================================================================
echo  ETAPA 3/5: Instalando dependencias Python...
echo ===================================================================
echo.
echo Isso pode levar alguns minutos...
echo.

echo Instalando dependencias...
pip install -r requirements.txt --quiet --disable-pip-version-check

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar algumas dependencias.
    echo Tentando instalar individualmente...
    echo.
    
    pip install selenium
    pip install gspread
    pip install google-auth
    pip install google-auth-oauthlib
    pip install google-auth-httplib2
    pip install google-api-python-client
    pip install pandas
    pip install python-dotenv
)

echo.
echo [OK] Todas as dependencias instaladas!
timeout /t 2 >nul

:: ============================================
:: ETAPA 4: CRIAR ESTRUTURA
:: ============================================
cls
echo.
echo ===================================================================
echo  ETAPA 4/5: Criando estrutura de pastas...
echo ===================================================================
echo.

if not exist "logs" mkdir logs
if not exist "temp_images" mkdir temp_images

echo [OK] Estrutura criada
timeout /t 2 >nul

:: ============================================
:: ETAPA 5: VERIFICAR CONFIGURACOES
:: ============================================
cls
echo.
echo ===================================================================
echo  ETAPA 5/5: Verificando configuracoes...
echo ===================================================================
echo.

set NEEDS_GOOGLE_SETUP=0
set NEEDS_AUTH=0

if not exist "credentials.json" (
    echo [PENDENTE] credentials.json nao encontrado
    set NEEDS_GOOGLE_SETUP=1
) else (
    echo [OK] credentials.json encontrado
)

if not exist "token.pickle" (
    echo [PENDENTE] token.pickle nao encontrado
    set NEEDS_AUTH=1
) else (
    echo [OK] token.pickle encontrado
)

if not exist ".env" (
    echo [AVISO] Arquivo .env nao encontrado
    echo Usando configuracoes padrao...
)

timeout /t 2 >nul

:: ============================================
:: INSTALACAO CONCLUIDA
:: ============================================
cls
echo.
echo ===================================================================
echo.
echo           INSTALACAO CONCLUIDA COM SUCESSO!
echo.
echo ===================================================================
echo.
echo STATUS DA CONFIGURACAO
echo ===================================================================
echo.

if %NEEDS_GOOGLE_SETUP%==1 (
    echo [PENDENTE] Configuracao do Google Cloud
    echo.
    echo   PROXIMOS PASSOS:
    echo   1. Acesse: https://console.cloud.google.com/
    echo   2. Crie projeto "Marketplace Automation"
    echo   3. Ative APIs: Google Sheets + Google Drive
    echo   4. Crie credencial OAuth 2.0 (Desktop app)
    echo   5. Baixe o JSON como "credentials.json"
    echo   6. Coloque nesta pasta: %CD%
    echo   7. Execute: SETUP_GOOGLE.bat
    echo.
) else (
    echo [OK] credentials.json configurado
)

if %NEEDS_AUTH%==1 (
    echo [PENDENTE] Autenticacao Google
    echo.
    echo   Execute: SETUP_GOOGLE.bat
    echo.
) else (
    echo [OK] Autenticacao Google configurada
)

echo.
echo ===================================================================
echo  ARQUIVOS IMPORTANTES
echo ===================================================================
echo.
echo   CONFIGURACAO.md  - Guia completo passo a passo
echo   README.md        - Documentacao detalhada
echo   .env             - Configuracoes (edite aqui)
echo.
echo   SETUP_GOOGLE.bat - Configurar autenticacao Google
echo   EXECUTAR.bat     - Rodar o script principal
echo.
echo ===================================================================
echo.

if %NEEDS_GOOGLE_SETUP%==1 (
    echo Deseja abrir o Google Cloud Console agora? (S/N)
    set /p RESPOSTA=Sua escolha: 
    if /i "%RESPOSTA%"=="S" start https://console.cloud.google.com/
)

echo.
echo Pressione qualquer tecla para abrir o guia de configuracao...
pause >nul

start CONFIGURACAO.md

echo.
echo ===================================================================
echo  Instalacao finalizada!
echo ===================================================================
echo.
pause
