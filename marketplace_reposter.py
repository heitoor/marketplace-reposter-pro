#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Facebook Marketplace Reposter - Automacao de repostagem
Versao 3.1 - Banco local (SQLite) + GUI
Desenvolvido por: Heitor
"""

import logging
import time
import random
import os
from datetime import datetime
from functools import wraps

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

# ===== Constantes =====
QUICK_DELAY = (0.5, 1)
SHORT_DELAY = (1, 2)
MEDIUM_DELAY = (3, 5)
LONG_DELAY = (5, 8)
PAGE_LOAD_WAIT = 4
SELENIUM_TIMEOUT = 20
MAX_RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY = 2


def retry(max_attempts=MAX_RETRY_ATTEMPTS, base_delay=RETRY_BASE_DELAY):
    """Decorator para retry com exponential backoff em operacoes Selenium."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (TimeoutException, NoSuchElementException) as e:
                    last_exception = e
                    if attempt < max_attempts:
                        wait_time = base_delay * (2 ** (attempt - 1))
                        logger.warning(
                            "Tentativa %d/%d falhou em %s: %s. Retentando em %ds...",
                            attempt, max_attempts, func.__name__, e, wait_time
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            "Todas as %d tentativas falharam em %s",
                            max_attempts, func.__name__
                        )
            raise last_exception
        return wrapper
    return decorator


class ReposterError(Exception):
    """Erro fatal do reposter (config, driver, etc.)"""
    pass


class MarketplaceReposter:
    """Automacao de repostagem no Facebook Marketplace"""

    def __init__(self, data_manager=None, login_callback=None, stop_event=None, progress_callback=None):
        self.login_callback = login_callback
        self.stop_event = stop_event
        self.progress_callback = progress_callback
        if data_manager is None:
            from data_layer.local_data_manager import LocalDataManager
            data_manager = LocalDataManager()
        self.data_manager = data_manager
        self.driver = None
        self.wait = None
        self.produtos_repostados = 0
        self.produtos_erro = 0

    def _check_stop(self):
        """Verifica se parada foi solicitada."""
        if self.stop_event and self.stop_event.is_set():
            raise ReposterError("Operacao cancelada pelo usuario.")

    def setup_driver(self):
        """Configura Chrome WebDriver com perfil persistente e anti-deteccao."""
        logger.info("Configurando navegador...")
        print("Configurando navegador...")

        try:
            from browser_setup import create_chrome_driver
            self.driver, self.wait = create_chrome_driver()
            print("Navegador configurado!\n")
        except RuntimeError as e:
            raise ReposterError(str(e))

    def human_delay(self, min_sec=None, max_sec=None):
        """Delay humanizado (interruptivel via stop_event)"""
        if min_sec is None:
            min_sec = float(os.getenv('MIN_DELAY', 3))
        if max_sec is None:
            max_sec = float(os.getenv('MAX_DELAY', 8))
        total = random.uniform(min_sec, max_sec)
        elapsed = 0
        while elapsed < total:
            self._check_stop()
            time.sleep(min(0.5, total - elapsed))
            elapsed += 0.5

    @staticmethod
    def _xpath_escape(text):
        """Escapa texto para uso seguro em expressoes XPath."""
        if "'" not in text:
            return f"'{text}'"
        if '"' not in text:
            return f'"{text}"'
        parts = text.split("'")
        return "concat(" + ",\"'\",".join(f"'{p}'" for p in parts) + ")"

    def _is_logged_in(self):
        """Verifica se o navegador esta logado no Facebook."""
        current = self.driver.current_url.lower()
        return 'marketplace' in current and 'login' not in current

    def check_login(self):
        """Verifica se ja esta logado no Facebook (perfil persistente)."""
        print("Verificando login no Facebook...")
        self.driver.get('https://www.facebook.com/marketplace')
        time.sleep(PAGE_LOAD_WAIT)

        if self._is_logged_in():
            print("Ja estava logado!\n")
            return True

        print("Faca login no Facebook na janela do Chrome...")
        if self.login_callback:
            self.login_callback()
        else:
            input("Pressione ENTER apos fazer login...")

        time.sleep(2)

        self.driver.get('https://www.facebook.com/marketplace')
        time.sleep(PAGE_LOAD_WAIT)

        if self._is_logged_in():
            print("Login concluido!\n")
            return True

        print("Login nao detectado. Verifique suas credenciais.\n")
        return False

    def remover_anuncio_antigo(self, link_anuncio):
        """Remove anuncio antigo pelo link. Retorna True se removido, False em erro."""
        if not link_anuncio or link_anuncio.strip() == '':
            print("  Sem link anterior, pulando remocao...")
            return True

        try:
            print("  Removendo anuncio antigo...")

            self.driver.get(link_anuncio)
            self.human_delay(*MEDIUM_DELAY)

            try:
                botao_opcoes = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//div[@aria-label='Mais opções' or @aria-label='More options' or contains(@aria-label, 'Ações')]"))
                )
                botao_opcoes.click()
                self.human_delay(*SHORT_DELAY)

                botao_excluir = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//span[contains(text(), 'Excluir') or contains(text(), 'Delete')]"))
                )
                botao_excluir.click()
                self.human_delay(*SHORT_DELAY)

                botao_confirmar = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//span[contains(text(), 'Excluir anúncio') or contains(text(), 'Delete listing')]"))
                )
                botao_confirmar.click()
                self.human_delay(2, 3)

                print("  Anuncio removido!")
                return True

            except TimeoutException:
                print("  Nao conseguiu remover (pode ja estar excluido)")
                logger.warning("Timeout ao remover anuncio: %s", link_anuncio)
                return True

        except Exception as e:
            logger.error("Erro ao remover anuncio %s: %s", link_anuncio, e, exc_info=True)
            print(f"  ERRO ao remover anuncio: {e}")
            return False

    @retry(max_attempts=2, base_delay=3)
    def criar_novo_anuncio(self, produto, imagens_locais):
        """Cria novo anuncio no Marketplace. Retorna (sucesso, link)."""
        try:
            print("  Criando novo anuncio...")

            self.driver.get('https://www.facebook.com/marketplace/create/item')
            self.human_delay(*MEDIUM_DELAY)

            # Upload de imagens
            if imagens_locais:
                print(f"  Upload de {len(imagens_locais)} imagens...")
                input_file = self.driver.find_element(By.XPATH, "//input[@type='file']")
                input_file.send_keys('\n'.join(imagens_locais))
                self.human_delay(*LONG_DELAY)

            # Titulo
            print("  Preenchendo titulo...")
            campo_titulo = self.wait.until(
                EC.presence_of_element_located((By.XPATH,
                    "//label[contains(text(), 'Título') or contains(text(), 'Title')]/following-sibling::div//input"))
            )
            campo_titulo.clear()
            self.human_delay(*QUICK_DELAY)
            campo_titulo.send_keys(produto['Título'])
            self.human_delay(*SHORT_DELAY)

            # Preco
            print("  Preenchendo preco...")
            campo_preco = self.driver.find_element(By.XPATH,
                "//label[contains(text(), 'Preço') or contains(text(), 'Price')]/following-sibling::div//input")
            campo_preco.clear()
            self.human_delay(*QUICK_DELAY)
            campo_preco.send_keys(str(produto['Preço']))
            self.human_delay(*SHORT_DELAY)

            # Categoria
            print("  Selecionando categoria...")
            try:
                campo_categoria = self.driver.find_element(By.XPATH,
                    "//label[contains(text(), 'Categoria') or contains(text(), 'Category')]/following-sibling::div")
                campo_categoria.click()
                self.human_delay(*SHORT_DELAY)

                categoria_texto = produto['Categoria'].split('>')[0].strip()
                cat_safe = self._xpath_escape(categoria_texto)
                opcao_categoria = self.driver.find_element(By.XPATH,
                    f"//span[contains(text(), {cat_safe})]")
                opcao_categoria.click()
                self.human_delay(*SHORT_DELAY)
            except (NoSuchElementException, TimeoutException):
                logger.warning("Categoria nao encontrada: %s", produto.get('Categoria', ''))
                print("  Categoria nao encontrada, continuando...")

            # Condicao
            print("  Selecionando condicao...")
            try:
                campo_condicao = self.driver.find_element(By.XPATH,
                    "//label[contains(text(), 'Condição') or contains(text(), 'Condition')]/following-sibling::div")
                campo_condicao.click()
                self.human_delay(*SHORT_DELAY)

                cond_safe = self._xpath_escape(produto['Condição'])
                opcao_condicao = self.driver.find_element(By.XPATH,
                    f"//span[text()={cond_safe}]")
                opcao_condicao.click()
                self.human_delay(*SHORT_DELAY)
            except (NoSuchElementException, TimeoutException):
                logger.warning("Condicao nao encontrada: %s", produto.get('Condição', ''))
                print("  Condicao nao encontrada, continuando...")

            # Descricao
            print("  Preenchendo descricao...")
            campo_descricao = self.driver.find_element(By.XPATH,
                "//label[contains(text(), 'Descrição') or contains(text(), 'Description')]/following-sibling::div//textarea")
            campo_descricao.clear()
            self.human_delay(*QUICK_DELAY)
            campo_descricao.send_keys(produto['Descrição'])
            self.human_delay(*SHORT_DELAY)

            # Localizacao
            print("  Preenchendo localizacao...")
            campo_localizacao = self.driver.find_element(By.XPATH,
                "//label[contains(text(), 'Localização') or contains(text(), 'Location')]/following-sibling::div//input")
            campo_localizacao.clear()
            self.human_delay(*QUICK_DELAY)
            campo_localizacao.send_keys(produto['Localização'])
            self.human_delay(2, 3)

            try:
                primeira_sugestao = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@role='option'][1]"))
                )
                primeira_sugestao.click()
                self.human_delay(*SHORT_DELAY)
            except TimeoutException:
                logger.warning("Nenhuma sugestao de localizacao apareceu")

            # Publicar
            print("  Publicando...")
            botao_publicar = self.wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//span[text()='Publicar' or text()='Publish' or text()='Avançar' or text()='Next']"))
            )
            botao_publicar.click()
            self.human_delay(*LONG_DELAY)

            # Capturar URL
            novo_link = self.driver.current_url
            if '/marketplace/item/' not in novo_link:
                print("  URL pos-publicacao nao e de anuncio, buscando link real...")
                self.driver.get('https://www.facebook.com/marketplace/you/selling')
                self.human_delay(*MEDIUM_DELAY)
                try:
                    primeiro_anuncio = self.driver.find_element(
                        By.CSS_SELECTOR, 'a[href*="/marketplace/item/"]')
                    novo_link = primeiro_anuncio.get_attribute('href').split('?')[0]
                except (NoSuchElementException, TimeoutException):
                    novo_link = ''
                    logger.warning("Nao conseguiu capturar link do anuncio apos publicacao")
                    print("  Nao conseguiu capturar link do anuncio")

            if novo_link:
                print(f"  Anuncio publicado! Link: {novo_link}")
            else:
                print("  Anuncio provavelmente publicado (link nao capturado)")

            return True, novo_link

        except (TimeoutException, NoSuchElementException):
            raise  # Deixa o decorator retry lidar
        except Exception as e:
            logger.error("Erro ao criar anuncio: %s", e, exc_info=True)
            print(f"  ERRO ao criar anuncio: {e}")
            return False, None

    def processar_produtos(self):
        """Processa todos os produtos"""
        produtos = self.data_manager.get_produtos_para_repostar()

        if not produtos:
            print("Nenhum produto para repostar.\n")
            return

        print("=" * 60)
        print(f"REPOSTANDO {len(produtos)} PRODUTOS")
        print("=" * 60 + "\n")

        for idx, produto in enumerate(produtos, 1):
            self._check_stop()

            if self.progress_callback:
                self.progress_callback(idx, len(produtos), produto['Título'])

            print(f"\n{'=' * 60}")
            print(f"PRODUTO {idx}/{len(produtos)}: {produto['Título']}")
            print(f"{'=' * 60}\n")

            # 1. Obter imagens
            imagens_locais = self.data_manager.get_imagens(produto)

            if not imagens_locais:
                print("  Sem imagens, pulando...\n")
                self.produtos_erro += 1
                continue

            # 2. Remover antigo
            removido = self.remover_anuncio_antigo(produto.get('Link Anúncio Atual', ''))
            if not removido:
                logger.warning("Falha ao remover anuncio antigo de %s, continuando mesmo assim",
                               produto['Título'])
            self.human_delay(*MEDIUM_DELAY)

            # 3. Criar novo
            sucesso, novo_link = self.criar_novo_anuncio(produto, imagens_locais)

            # 4. Atualizar banco de dados
            if sucesso:
                data_hoje = datetime.now().strftime('%Y-%m-%d')
                self.data_manager.atualizar_apos_postagem(
                    produto['id'], data_hoje, novo_link, True
                )
                self.produtos_repostados += 1
            else:
                self.data_manager.atualizar_apos_postagem(
                    produto['id'], '', '', False
                )
                self.produtos_erro += 1

            # 5. Delay interruptivel com countdown
            if idx < len(produtos):
                delay = int(os.getenv('DELAY_BETWEEN_POSTS', 420))
                print(f"Aguardando {delay}s ate o proximo anuncio...")
                elapsed = 0
                while elapsed < delay:
                    self._check_stop()
                    remaining = delay - elapsed
                    if remaining % 60 == 0 and remaining > 0:
                        print(f"  {int(remaining)}s restantes...")
                    time.sleep(min(1, remaining))
                    elapsed += 1

        self.data_manager.limpar_temp_images()

        print("\n" + "=" * 60)
        print("CONCLUIDO!")
        print("=" * 60)
        print(f"Repostados: {self.produtos_repostados}")
        print(f"Erros: {self.produtos_erro}")
        print("=" * 60 + "\n")

    def run(self):
        """Executa processo completo"""
        try:
            print("\n" + "=" * 60)
            from gui.utils.paths import APP_VERSION
            print(f"FACEBOOK MARKETPLACE REPOSTER v{APP_VERSION}")
            print("Banco Local + Automacao Selenium")
            print("=" * 60 + "\n")

            self.setup_driver()

            if not self.check_login():
                return

            self.processar_produtos()

            print("\nProcesso finalizado!\n")
            if not self.login_callback:  # Modo CLI
                input("Pressione ENTER para sair...")

        except KeyboardInterrupt:
            print("\n\nInterrompido pelo usuario!")
            logger.info("Execucao interrompida via KeyboardInterrupt")
        except ReposterError as e:
            print(f"\n{e}")
            logger.error("ReposterError: %s", e)
        except Exception as e:
            logger.error("Erro inesperado: %s", e, exc_info=True)
            print(f"\nErro inesperado: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver encerrado")


if __name__ == "__main__":
    from dotenv import load_dotenv
    from gui.utils.paths import get_env_path, get_data_dir
    load_dotenv(get_env_path())
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(get_data_dir() / 'reposter.log', encoding='utf-8'),
            logging.StreamHandler(),
        ]
    )
    reposter = MarketplaceReposter()
    reposter.run()
