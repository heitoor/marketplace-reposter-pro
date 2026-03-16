@echo off
chcp 65001 >nul
title Setup Autenticação Google - Marketplace Reposter
color 0B

cls
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║        SETUP AUTENTICAÇÃO GOOGLE                         ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

:: Verificar se credentials.json existe
if not exist "credentials.json" (
    echo ❌ Arquivo credentials.json não encontrado!
    echo.
    echo ═══════════════════════════════════════════════════════════
    echo  COMO OBTER O ARQUIVO credentials.json
    echo ═══════════════════════════════════════════════════════════
    echo.
    echo 1. Acesse: https://console.cloud.google.com/
    echo 2. Crie novo projeto: "Marketplace Automation"
    echo 3. Ative as APIs:
    echo    - Google Sheets API
    echo    - Google Drive API
    echo 4. Vá em: APIs ^& Services ^> Credentials
    echo 5. Create Credentials ^> OAuth client ID
    echo 6. Application type: Desktop app
    echo 7. Baixe o JSON
    echo 8. Renomeie para: credentials.json
    echo 9. Coloque nesta pasta: %CD%
    echo 10. Execute este script novamente
    echo.
    echo Deseja abrir o Google Cloud Console? (S/N^)
    choice /c SN /n
    if errorlevel 2 goto end
    if errorlevel 1 start https://console.cloud.google.com/
    goto end
)

echo ✓ credentials.json encontrado!
echo.
echo ═══════════════════════════════════════════════════════════
echo  INICIANDO AUTENTICAÇÃO
echo ═══════════════════════════════════════════════════════════
echo.
echo Uma janela do navegador vai abrir.
echo.
echo Instruções:
echo   1. Faça login na sua conta Google
echo   2. Autorize o acesso ao Google Sheets e Drive
echo   3. Volte aqui após autorizar
echo.
echo Pressione qualquer tecla para continuar...
pause >nul

echo.
echo Executando autenticação...
echo.

python google_auth_setup.py

if %errorLevel% equ 0 (
    echo.
    echo ═══════════════════════════════════════════════════════════
    echo  ✓ AUTENTICAÇÃO CONCLUÍDA COM SUCESSO!
    echo ═══════════════════════════════════════════════════════════
    echo.
    echo Arquivo token.pickle foi criado.
    echo.
    echo ═══════════════════════════════════════════════════════════
    echo  PRÓXIMOS PASSOS
    echo ═══════════════════════════════════════════════════════════
    echo.
    echo 1. Crie sua planilha no Google Sheets
    echo 2. Use o template em: TEMPLATE_PLANILHA.md
    echo 3. Copie o ID da planilha da URL
    echo 4. Edite o arquivo .env
    echo 5. Cole o ID em: GOOGLE_SHEET_ID=
    echo 6. Organize fotos no Google Drive
    echo 7. Execute: EXECUTAR.bat
    echo.
) else (
    echo.
    echo ═══════════════════════════════════════════════════════════
    echo  ❌ ERRO NA AUTENTICAÇÃO
    echo ═══════════════════════════════════════════════════════════
    echo.
    echo Verifique:
    echo   - credentials.json está correto
    echo   - Você autorizou o acesso
    echo   - Sua conexão com internet
    echo.
    echo Tente executar novamente este script.
    echo.
)

:end
echo.
pause
