# 🚀 INSTALAÇÃO RÁPIDA - MARKETPLACE REPOSTER

## ⚡ 3 CLIQUES E PRONTO!

### CLIQUE 1: INSTALAR.bat
```
📁 D:\MarketPlace\
   └── 🖱️ Clique duplo em: INSTALAR.bat
       (Clique direito > Executar como Administrador)
```

**O que acontece:**
- ✅ Verifica Python
- ✅ Instala todas as bibliotecas
- ✅ Configura ChromeDriver
- ✅ Cria estrutura de pastas

**Tempo:** ~3-5 minutos

---

### CLIQUE 2: SETUP_GOOGLE.bat
```
📁 D:\MarketPlace\
   └── 🖱️ Clique duplo em: SETUP_GOOGLE.bat
```

**Antes de executar:**
1. Acesse: https://console.cloud.google.com/
2. Crie projeto: "Marketplace Automation"
3. Ative APIs: Google Sheets + Drive
4. Baixe credentials.json
5. Coloque em D:\MarketPlace\

**O que acontece:**
- 🌐 Abre navegador para login Google
- ✅ Autoriza acesso à planilha e drive
- ✅ Salva autenticação

**Tempo:** ~2 minutos

---

### CLIQUE 3: EXECUTAR.bat
```
📁 D:\MarketPlace\
   └── 🖱️ Clique duplo em: EXECUTAR.bat
```

**Antes de executar:**
1. Crie planilha Google Sheets
2. Copie ID da planilha
3. Edite .env e cole o ID
4. Organize fotos no Google Drive
5. Preencha planilha

**O que acontece:**
- 🤖 Login automático no Facebook
- 🔍 Busca produtos >7 dias
- 📷 Baixa fotos do Drive
- 🗑️ Remove anúncios antigos
- 📝 Cria novos anúncios
- ✅ Atualiza planilha

**Tempo:** Varia conforme número de produtos

---

## 📋 CHECKLIST COMPLETO

```
☐ 1. Baixar e extrair arquivos para D:\MarketPlace
☐ 2. Clique duplo: INSTALAR.bat (como Administrador)
☐ 3. Aguardar instalação completar
☐ 4. Acessar Google Cloud Console
☐ 5. Criar projeto e ativar APIs
☐ 6. Baixar credentials.json
☐ 7. Colocar credentials.json em D:\MarketPlace
☐ 8. Clique duplo: SETUP_GOOGLE.bat
☐ 9. Fazer login e autorizar
☐ 10. Criar planilha Google Sheets
☐ 11. Copiar ID da planilha
☐ 12. Editar .env e colar ID
☐ 13. Organizar fotos no Google Drive
☐ 14. Preencher planilha com produtos
☐ 15. Clique duplo: EXECUTAR.bat
☐ 16. Fazer login Facebook (primeira vez)
☐ 17. Aguardar repostagem completar
```

---

## 🎯 FLUXO VISUAL

```
┌─────────────────────────────────────────────────────────┐
│  PREPARAÇÃO (Uma vez só)                                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. INSTALAR.bat                                        │
│     ↓                                                    │
│     Instala Python, dependências, ChromeDriver          │
│                                                          │
│  2. Google Cloud Console                                │
│     ↓                                                    │
│     Cria projeto, ativa APIs, baixa credentials.json   │
│                                                          │
│  3. SETUP_GOOGLE.bat                                    │
│     ↓                                                    │
│     Autentica e salva token                             │
│                                                          │
│  4. Criar e preencher planilha                          │
│     ↓                                                    │
│     Google Sheets com produtos e fotos no Drive         │
│                                                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  USO SEMANAL (A cada 7 dias)                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  EXECUTAR.bat                                           │
│     ↓                                                    │
│     Reposta produtos automaticamente                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ SE ALGO DER ERRADO

### Python não encontrado
```bash
# Baixe e instale:
https://www.python.org/downloads/

# IMPORTANTE: Marque "Add Python to PATH"
```

### ChromeDriver incompatível
```bash
# Verifique versão do Chrome:
chrome://version

# Baixe versão correspondente:
https://chromedriver.chromium.org/
```

### Erro de autenticação Google
```bash
# Delete e refaça:
del token.pickle
SETUP_GOOGLE.bat
```

### Planilha não atualiza
```bash
# Verifique no .env:
GOOGLE_SHEET_ID=SEU_ID_CORRETO_AQUI
```

---

## 💡 DICAS PRO

### Agendamento Automático (Windows)
```
1. Win + R > digitar: taskschd.msc
2. Criar Tarefa Básica
3. Nome: "Marketplace Reposter"
4. Gatilho: Semanalmente (toda segunda 10h)
5. Ação: Iniciar programa
6. Programa: D:\MarketPlace\EXECUTAR.bat
```

### Backup Automático
```bash
# Copie periodicamente:
D:\MarketPlace\token.pickle
D:\MarketPlace\fb_cookies.pkl
D:\MarketPlace\.env
```

### Logs de Erro
```bash
# Verifique em caso de problemas:
D:\MarketPlace\logs\
```

---

## ✅ PRONTO PARA USAR!

Agora é só:
1. Extrair arquivos em D:\MarketPlace
2. Clique duplo: INSTALAR.bat
3. Seguir as instruções na tela

**Tudo está automatizado!** 🚀

---

Precisa de ajuda? Consulte:
- README.md (documentação completa)
- CONFIGURACAO.md (passo a passo detalhado)
- TEMPLATE_PLANILHA.md (modelo da planilha)
