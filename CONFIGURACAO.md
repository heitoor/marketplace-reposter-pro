# Configuracao - Marketplace Reposter Pro v3.x

> **NOTA:** A partir da versao 3.0, o app usa banco de dados local (SQLite).
> Nao e mais necessario configurar Google Sheets ou Google Drive.

## Requisitos

1. **Python 3.10+** - https://www.python.org/downloads/
2. **Google Chrome** - https://www.google.com/chrome/

## Instalacao

### Via instalador
Baixe o instalador da pagina de releases e execute.

### Via codigo-fonte
```bash
pip install -r requirements.txt
python gui_app.py
```

## Configuracao do .env

O arquivo `.env` fica em `%LOCALAPPDATA%\MarketplaceReposterPro\.env`.
E criado automaticamente na primeira execucao.

```env
# Delay entre acoes (segundos)
MIN_DELAY=3
MAX_DELAY=8

# Delay entre produtos (segundos)
DELAY_BETWEEN_POSTS=420

# Intervalo de repostagem (dias)
REPOST_INTERVAL_DAYS=7

# Navegador invisivel
HEADLESS=False
```

## Login no Facebook

1. Abra o app
2. Clique em "Login no Facebook"
3. Faca login na janela do Chrome
4. Clique em "Login Concluido" no app
5. A sessao e salva automaticamente

## Importar anuncios

1. Na aba "Meus Anuncios", clique em "Importar do Facebook"
2. O app coleta automaticamente seus anuncios existentes
3. Titulos, precos, imagens e descricoes sao salvos localmente

## Backup

O app cria backups em `%LOCALAPPDATA%\MarketplaceReposterPro\backups\`.
Voce tambem pode exportar seus dados via CSV ou JSON.
