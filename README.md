# 🚀 Facebook Marketplace Reposter

Automação para repostar anúncios no Facebook Marketplace a cada 7 dias.

Integração com **Google Sheets** (gerenciar produtos) + **Google Drive** (armazenar fotos).

---

## 📋 PRÉ-REQUISITOS

### 1. Python 3.8+
- Download: https://www.python.org/downloads/
- Durante instalação: ✅ Marque "Add Python to PATH"

### 2. Google Chrome
- Download: https://www.google.com/chrome/

### 3. ChromeDriver
- Download: https://chromedriver.chromium.org/
- Versão deve corresponder à sua versão do Chrome
- Verifique sua versão: chrome://version
- Extraia e coloque o `chromedriver.exe` na pasta do projeto

### 4. Conta Google
- Para acessar Sheets e Drive

---

## 🔧 INSTALAÇÃO

### Passo 1: Instalar Dependências

Abra o Prompt de Comando nesta pasta e execute:

```bash
pip install -r requirements.txt
```

### Passo 2: Configurar Google Cloud

1. Acesse: https://console.cloud.google.com/
2. Crie novo projeto: "Marketplace Automation"
3. Ative as APIs:
   - Google Sheets API
   - Google Drive API
4. Criar credenciais OAuth 2.0:
   - APIs & Services > Credentials
   - Create Credentials > OAuth client ID
   - Application type: **Desktop app**
   - Nome: "Marketplace Reposter"
   - Download JSON
5. Renomeie o arquivo baixado para: **credentials.json**
6. Coloque na pasta deste projeto

### Passo 3: Configurar Autenticação

Execute o script de setup:

```bash
python google_auth_setup.py
```

- Uma janela do navegador vai abrir
- Faça login na sua conta Google
- Autorize o acesso
- Arquivo `token.pickle` será criado

### Passo 4: Criar Google Sheet

1. Acesse: https://sheets.google.com/
2. Criar nova planilha: "Marketplace - Produtos"
3. Adicionar colunas (ORDEM EXATA):
   - **A**: ID
   - **B**: Título
   - **C**: Descrição
   - **D**: Preço
   - **E**: Categoria
   - **F**: Condição
   - **G**: Localização
   - **H**: Pasta Drive
   - **I**: Link Anúncio Atual
   - **J**: Data Publicação
   - **K**: Status
   - **L**: Última Ação

4. Copiar ID da planilha da URL:
   ```
   https://docs.google.com/spreadsheets/d/SEU_ID_AQUI/edit
   ```

### Passo 5: Configurar .env

Abra o arquivo `.env` e configure:

```env
GOOGLE_SHEET_ID=COLE_SEU_ID_AQUI
```

### Passo 6: Organizar Fotos no Google Drive

1. Crie uma pasta: "Marketplace Fotos"
2. Para cada produto, crie uma subpasta
3. Coloque as fotos do produto na subpasta
4. Clique direito na pasta > Compartilhar
5. Alterar para: "Qualquer pessoa com o link"
6. Copiar link da pasta
7. Colar na coluna "Pasta Drive" da planilha

**Estrutura recomendada:**
```
Google Drive/
├── Marketplace Fotos/
│   ├── iPhone 12/
│   │   ├── foto1.jpg
│   │   ├── foto2.jpg
│   │   └── foto3.jpg
│   ├── Notebook Dell/
│   │   └── foto1.jpg
│   └── Sofá/
│       ├── foto1.jpg
│       └── foto2.jpg
```

---

## 🎯 COMO USAR

### Primeira Execução

```bash
python marketplace_reposter.py
```

1. Script abre Chrome
2. Faça login no Facebook manualmente
3. Pressione ENTER no terminal
4. Sessão será salva para próximas vezes

### Execuções Seguintes (a cada 7 dias)

```bash
python marketplace_reposter.py
```

O script vai:
1. ✅ Conectar no Google Sheets
2. ✅ Buscar produtos com >7 dias desde última postagem
3. ✅ Baixar fotos do Google Drive
4. ✅ Remover anúncios antigos
5. ✅ Criar novos anúncios
6. ✅ Atualizar planilha com novos links
7. ✅ Registrar data de publicação

---

## 📊 EXEMPLO DE PLANILHA

| ID | Título | Descrição | Preço | Categoria | Condição | Localização | Pasta Drive | Link Anúncio Atual | Data Publicação | Status | Última Ação |
|----|--------|-----------|-------|-----------|----------|-------------|-------------|-------------------|-----------------|--------|-------------|
| 1 | iPhone 12 64GB | iPhone 12... | 1899 | Eletrônicos > Celulares | Usado | Londrina-PR | https://drive.google.com/... | https://facebook.com/... | 2025-03-01 | ativo | Repostado em 01/03 |

**Campos importantes:**
- **Status**: "ativo", "vendido", "pausado"
- **Data Publicação**: Formato AAAA-MM-DD
- **Pasta Drive**: Link da pasta com fotos

---

## ⚙️ CONFIGURAÇÕES

Edite o arquivo `.env` para ajustar:

```env
# Delay entre ações (segundos)
MIN_DELAY=3
MAX_DELAY=8

# Delay entre produtos (segundos) - recomendado 5-10min
DELAY_BETWEEN_POSTS=420

# Modo headless (True = navegador invisível)
HEADLESS=False
```

---

## ⚠️ DICAS IMPORTANTES

### Segurança
- ✅ Rode durante horário comercial (9h-18h)
- ✅ Não rode mais de 1x por semana
- ✅ Máximo 10 produtos por vez
- ✅ Use delay de 5-10min entre produtos

### Fotos
- ✅ Imagens diferentes para cada produto
- ✅ Boa qualidade (mínimo 720x720)
- ✅ Máximo 10 fotos por produto

### Textos
- ✅ Varie ligeiramente descrições
- ✅ Não use textos 100% idênticos
- ✅ Emojis são permitidos (com moderação)

---

## 🐛 SOLUÇÃO DE PROBLEMAS

### Erro: "ChromeDriver não encontrado"
- Baixe ChromeDriver: https://chromedriver.chromium.org/
- Coloque na pasta do projeto
- Ou adicione ao PATH do Windows

### Erro: "Token expirado"
```bash
# Delete o token e refaça autenticação
del token.pickle
python google_auth_setup.py
```

### Erro: "Não conseguiu remover anúncio"
- Normal se anúncio já foi removido
- Script continua normalmente

### Erro: "Imagens não encontradas"
- Verifique permissões da pasta no Drive
- Link deve estar como "Qualquer pessoa com o link"

---

## 📁 ESTRUTURA DE ARQUIVOS

```
marketplace-reposter/
├── marketplace_reposter.py    # Script principal
├── google_auth_setup.py       # Setup autenticação
├── requirements.txt           # Dependências
├── .env                      # Configurações
├── credentials.json          # Credenciais Google (você cria)
├── token.pickle             # Token autenticação (auto)
├── fb_cookies.pkl           # Sessão Facebook (auto)
├── temp_images/             # Imagens temporárias (auto)
└── README.md               # Este arquivo
```

---

## 📞 SUPORTE

Se encontrar problemas:
1. Verifique se seguiu TODOS os passos
2. Confira os logs de erro
3. Teste com 1 produto primeiro

---

## 📝 CHANGELOG

### v2.0 (Atual)
- ✅ Integração Google Sheets
- ✅ Integração Google Drive
- ✅ Download automático de fotos
- ✅ Registro de links de anúncios
- ✅ Registro de datas
- ✅ Logs detalhados

---

Desenvolvido com ❤️ por Heitor
