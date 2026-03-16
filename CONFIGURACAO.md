# ⚡ GUIA RÁPIDO DE CONFIGURAÇÃO

## 📝 CHECKLIST DE SETUP

### ☐ 1. INSTALAR PYTHON
- [ ] Baixar: https://www.python.org/downloads/
- [ ] Durante instalação: MARCAR "Add Python to PATH"
- [ ] Testar no CMD: `python --version`

### ☐ 2. INSTALAR DEPENDÊNCIAS
```bash
cd caminho\para\marketplace-reposter
pip install -r requirements.txt
```

### ☐ 3. BAIXAR CHROMEDRIVER
- [ ] Verificar versão Chrome: chrome://version
- [ ] Baixar: https://chromedriver.chromium.org/
- [ ] Extrair chromedriver.exe para esta pasta

### ☐ 4. CONFIGURAR GOOGLE CLOUD
- [ ] Acessar: https://console.cloud.google.com/
- [ ] Criar projeto: "Marketplace Automation"
- [ ] Ativar APIs:
  - [ ] Google Sheets API
  - [ ] Google Drive API
- [ ] Criar credencial OAuth 2.0 (Desktop app)
- [ ] Baixar JSON e renomear para: credentials.json
- [ ] Colocar credentials.json nesta pasta

### ☐ 5. AUTENTICAR GOOGLE
```bash
python google_auth_setup.py
```
- [ ] Fazer login quando navegador abrir
- [ ] Autorizar acesso
- [ ] Confirmar criação de token.pickle

### ☐ 6. CRIAR PLANILHA GOOGLE
- [ ] Criar em: https://sheets.google.com/
- [ ] Nome: "Marketplace - Produtos"
- [ ] Adicionar colunas (ordem exata):
  ```
  A: ID
  B: Título
  C: Descrição
  D: Preço
  E: Categoria
  F: Condição
  G: Localização
  H: Pasta Drive
  I: Link Anúncio Atual
  J: Data Publicação
  K: Status
  L: Última Ação
  ```
- [ ] Copiar ID da URL da planilha

### ☐ 7. CONFIGURAR .ENV
- [ ] Abrir arquivo .env
- [ ] Colar ID da planilha em: GOOGLE_SHEET_ID=

### ☐ 8. ORGANIZAR FOTOS NO DRIVE
- [ ] Criar pasta: "Marketplace Fotos"
- [ ] Para cada produto:
  - [ ] Criar subpasta
  - [ ] Upload de fotos
  - [ ] Compartilhar: "Qualquer pessoa com o link"
  - [ ] Copiar link
  - [ ] Colar na coluna H da planilha

### ☐ 9. PREENCHER PLANILHA
- [ ] Adicionar produtos na planilha
- [ ] Status: "ativo"
- [ ] Links das pastas do Drive

### ☐ 10. PRIMEIRA EXECUÇÃO
```bash
python marketplace_reposter.py
```
ou
```bash
EXECUTAR.bat
```
- [ ] Fazer login no Facebook quando solicitado
- [ ] Aguardar script terminar

---

## 🎯 USO SEMANAL (após setup)

**A cada 7 dias:**
1. Clique duplo em: `EXECUTAR.bat`
2. Aguarde processo completar
3. Verifique planilha atualizada

---

## 📊 EXEMPLO DE LINHA NA PLANILHA

| A | B | C | D | E | F | G | H | I | J | K | L |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | iPhone 12 64GB | iPhone em ótimo estado... | 1899 | Eletrônicos > Celulares | Usado | Londrina-PR | https://drive.google.com/drive/folders/ABC123 | https://facebook.com/marketplace/item/789 | 2025-03-01 | ativo | Repostado em 01/03/2025 10:30 |

---

## ⚠️ PROBLEMAS COMUNS

### Python não reconhecido
```
Reinstale Python marcando "Add to PATH"
```

### ChromeDriver erro
```
Verifique versão do Chrome vs ChromeDriver
Coloque chromedriver.exe na pasta do projeto
```

### Erro de autenticação Google
```
del token.pickle
python google_auth_setup.py
```

### Imagens não baixam
```
Verifique permissões no Drive
Link deve ser: "Qualquer pessoa com o link"
```

---

## 💡 DICAS

✅ Teste com 1-2 produtos primeiro
✅ Rode durante horário comercial
✅ Não rode mais de 1x por semana
✅ Use fotos diferentes para cada produto
✅ Varie ligeiramente as descrições

---

**Pronto! Agora você está configurado. 🚀**

Qualquer dúvida, consulte o README.md completo.
