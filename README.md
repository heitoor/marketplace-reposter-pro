# Marketplace Reposter Pro

Automacao profissional para repostar anuncios no Facebook Marketplace.

Interface grafica (GUI) com banco de dados local, importacao automatica e repostagem agendada.

---

## Pre-requisitos

### 1. Python 3.10+
- Download: https://www.python.org/downloads/
- Durante instalacao: marque "Add Python to PATH"

### 2. Google Chrome
- Download: https://www.google.com/chrome/
- O ChromeDriver e baixado automaticamente pelo Selenium

---

## Instalacao

### Opcao A: Instalador (recomendado)

1. Baixe o instalador da [pagina de releases](../../releases)
2. Execute `MarketplaceReposterPro_Setup_vX.X.X.exe`
3. Siga as instrucoes do instalador

### Opcao B: Via codigo-fonte

```bash
pip install -r requirements.txt
python gui_app.py
```

Ou simplesmente execute o `EXECUTAR.bat`.

---

## Como usar

### 1. Login no Facebook

- Clique em **"Login no Facebook"** na tela principal
- Uma janela do Chrome vai abrir
- Faca login normalmente
- A sessao e salva automaticamente para as proximas vezes

### 2. Importar anuncios existentes

- Na aba **"Meus Anuncios"**, clique em **"Importar do Facebook"**
- O app navega ate sua pagina de vendas e importa todos os anuncios
- Titulos, precos, descricoes e imagens sao salvos localmente

### 3. Criar anuncio manualmente

- Clique em **"+ Novo"** na aba "Meus Anuncios"
- Preencha os campos e adicione imagens
- O anuncio sera salvo localmente e publicado na proxima repostagem

### 4. Repostar

- Na aba **"Repostagem"**, clique em **"Iniciar"**
- O app reposta automaticamente todos os anuncios ativos com mais de 7 dias
- Acompanhe o progresso no log em tempo real

---

## Configuracoes

Edite as configuracoes na aba "Repostagem" > botao de engrenagem, ou diretamente no `.env`:

```env
# Delay entre acoes do Selenium (segundos)
MIN_DELAY=3
MAX_DELAY=8

# Delay entre produtos (segundos) - recomendado 5-10min
DELAY_BETWEEN_POSTS=420

# Intervalo para repostagem (dias)
REPOST_INTERVAL_DAYS=7

# Modo headless (True = navegador invisivel)
HEADLESS=False
```

---

## Funcionalidades

- **Interface grafica** moderna com CustomTkinter (dark mode)
- **Banco de dados local** SQLite (sem depender de Google Sheets)
- **Importacao automatica** de anuncios existentes do Facebook
- **Repostagem inteligente** - so reposta anuncios com mais de X dias
- **Anti-deteccao** - delays humanizados, perfil persistente, fingerprint
- **Gerenciamento completo** - criar, editar, excluir, buscar anuncios
- **Status por anuncio** - ativo, pausado, vendido
- **Export/Import** - CSV e JSON para backup ou migracao
- **Backup automatico** do banco de dados
- **Atualizacao automatica** - notifica quando ha versao nova
- **Instalador profissional** com Inno Setup

---

## Dicas de seguranca

- Rode durante horario comercial (9h-18h)
- Nao rode mais de 1x por semana
- Maximo 10-15 produtos por sessao
- Use delay de 5-10min entre produtos
- Varie descricoes levemente entre repostagens

---

## Solucao de problemas

### Chrome nao abre
- Certifique-se de ter o Google Chrome instalado
- O Selenium baixa o ChromeDriver automaticamente

### Login nao funciona
- Faca login manualmente na janela do Chrome
- Clique em "Login Concluido" no app
- A sessao e salva para as proximas vezes

### Anuncio nao removido
- Normal se o anuncio ja foi removido pelo Facebook
- O app continua com o proximo anuncio

---

## Estrutura do projeto

```
MarketplaceReposterPro/
├── gui_app.py                 # Entry point (GUI)
├── marketplace_reposter.py    # Automacao de repostagem
├── marketplace_scraper.py     # Importacao de anuncios
├── browser_setup.py           # Configuracao compartilhada do Chrome
├── gui/                       # Interface grafica
│   ├── main_window.py         # Janela principal
│   ├── frames/                # Componentes da GUI
│   ├── workers/               # Threads de background
│   └── utils/                 # Tema, paths, settings
├── data_layer/                # Banco de dados
│   ├── database.py            # SQLite wrapper
│   ├── local_data_manager.py  # CRUD + export/import
│   └── image_manager.py       # Gerenciamento de imagens
├── tests/                     # Suite de testes (pytest)
├── assets/                    # Icone e recursos
├── requirements.txt           # Dependencias
└── installer.iss              # Script do instalador
```

Dados do usuario ficam em `%LOCALAPPDATA%\MarketplaceReposterPro\`:
- `reposter.db` - Banco de dados
- `images/` - Imagens dos anuncios
- `chrome_profile/` - Sessao do Facebook
- `.env` - Configuracoes
- `backups/` - Backups automaticos

---

## Desenvolvimento

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

---

Desenvolvido por Heitor - EITO LABS
