#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup inicial da autenticação Google
Execute este arquivo UMA vez para gerar o token de acesso
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

# Escopos necessários
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly'
]

def setup_google_auth():
    """Configura autenticação Google OAuth"""
    creds = None
    
    # Verifica se já existe token salvo
    if os.path.exists('token.pickle'):
        print("✅ Token existente encontrado!")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Se não existe ou está inválido, faz novo login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Renovando token...")
            creds.refresh(Request())
        else:
            print("\n" + "="*60)
            print("CONFIGURAÇÃO INICIAL - AUTENTICAÇÃO GOOGLE")
            print("="*60)
            print("\nPasso a passo:")
            print("1. Uma janela do navegador vai abrir")
            print("2. Faça login na sua conta Google")
            print("3. Autorize o acesso às planilhas e drive")
            print("4. Volte aqui após autorizar")
            print("="*60 + "\n")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salva token para próximas execuções
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        
        print("✅ Autenticação configurada com sucesso!")
        print("✅ Token salvo em: token.pickle\n")
    
    return creds

if __name__ == "__main__":
    print("\n🔐 SETUP DE AUTENTICAÇÃO GOOGLE\n")
    
    if not os.path.exists('credentials.json'):
        print("❌ Arquivo 'credentials.json' não encontrado!")
        print("\n📋 INSTRUÇÕES PARA OBTER O ARQUIVO:")
        print("="*60)
        print("1. Acesse: https://console.cloud.google.com/")
        print("2. Crie um projeto novo (ex: 'Marketplace Automation')")
        print("3. Ative as APIs:")
        print("   - Google Sheets API")
        print("   - Google Drive API")
        print("4. Vá em: APIs & Services > Credentials")
        print("5. Clique em: Create Credentials > OAuth client ID")
        print("6. Application type: Desktop app")
        print("7. Baixe o arquivo JSON")
        print("8. Renomeie para 'credentials.json'")
        print("9. Coloque na pasta deste script")
        print("="*60)
        print("\nDepois de fazer isso, rode este script novamente.\n")
        input("Pressione ENTER para sair...")
        exit(1)
    
    setup_google_auth()
    print("✅ Pronto! Agora você pode usar o script principal.\n")
    input("Pressione ENTER para sair...")
