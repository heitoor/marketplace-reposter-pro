# INSTALACAO RAPIDA - MARKETPLACE REPOSTER PRO

## Via Instalador (recomendado)

1. Baixe o instalador da pagina de releases
2. Execute `MarketplaceReposterPro_Setup_vX.X.X.exe`
3. Abra o app pelo atalho na area de trabalho

## Via Codigo-Fonte

### 1. INSTALAR.bat
Execute para instalar Python e dependencias automaticamente.

### 2. EXECUTAR.bat
Abre a interface grafica do app.

## Primeiro uso

1. Clique em **"Login no Facebook"**
2. Faca login na janela do Chrome
3. Seus anuncios serao importados automaticamente
4. Na aba "Repostagem", clique em **"Iniciar"** para repostar

## Agendamento automatico

Para rodar semanalmente, use o Agendador de Tarefas do Windows:
1. Abra `taskschd.msc`
2. Crie tarefa basica
3. Trigger: Semanal
4. Acao: Iniciar programa > caminho do `gui_app.py`
