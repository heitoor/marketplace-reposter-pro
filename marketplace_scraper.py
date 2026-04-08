#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Facebook Marketplace Scraper - Importa anuncios existentes do usuario.
Navega ate a pagina de vendas, coleta dados de cada anuncio e salva localmente.
"""

import logging
import os
import time
import random
import urllib.request
from datetime import datetime
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from gui.utils.paths import get_images_dir

logger = logging.getLogger(__name__)

# Constantes
MAX_IMAGES_PER_LISTING = 10
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 5000
MAX_LOCATION_LENGTH = 100
SCROLL_STABILIZATION_ATTEMPTS = 3
SELENIUM_TIMEOUT = 20
PAGE_LOAD_WAIT = 4
IMAGE_DOWNLOAD_TIMEOUT = 30
MIN_IMAGE_WIDTH = 100


class ScraperError(Exception):
    """Erro fatal do scraper."""
    pass


def validate_listing_data(data: dict) -> dict:
    """Valida e sanitiza dados extraidos de um anuncio."""
    # Titulo
    titulo = str(data.get('titulo', '')).strip()
    if len(titulo) > MAX_TITLE_LENGTH:
        titulo = titulo[:MAX_TITLE_LENGTH]
    data['titulo'] = titulo

    # Preco
    preco = data.get('preco', 0)
    try:
        preco = float(preco)
        if preco < 0:
            preco = 0
    except (ValueError, TypeError):
        preco = 0
    data['preco'] = preco

    # Descricao
    descricao = str(data.get('descricao', '')).strip()
    if len(descricao) > MAX_DESCRIPTION_LENGTH:
        descricao = descricao[:MAX_DESCRIPTION_LENGTH]
    data['descricao'] = descricao

    # Localizacao
    localizacao = str(data.get('localizacao', '')).strip()
    if len(localizacao) > MAX_LOCATION_LENGTH:
        localizacao = localizacao[:MAX_LOCATION_LENGTH]
    data['localizacao'] = localizacao

    # Link
    link = str(data.get('link_anuncio', '')).strip()
    if link and not link.startswith('https://'):
        link = ''
    data['link_anuncio'] = link

    # Imagens - limitar quantidade
    image_urls = data.get('image_urls', [])
    data['image_urls'] = image_urls[:MAX_IMAGES_PER_LISTING]

    return data


class MarketplaceScraper:
    """Importa anuncios do Facebook Marketplace do usuario."""

    SELLING_URL = "https://www.facebook.com/marketplace/you/selling"

    def __init__(self, data_manager=None, login_callback=None,
                 stop_event=None, progress_callback=None):
        self.data_manager = data_manager
        self.login_callback = login_callback
        self.stop_event = stop_event
        self.progress_callback = progress_callback
        self.driver = None
        self.wait = None
        self.imported_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def _check_stop(self):
        if self.stop_event and self.stop_event.is_set():
            raise ScraperError("Operacao cancelada pelo usuario.")

    def setup_driver(self):
        """Configura Chrome WebDriver com perfil persistente."""
        logger.info("Configurando navegador...")
        print("Configurando navegador...")

        try:
            from browser_setup import create_chrome_driver
            self.driver, self.wait = create_chrome_driver()
            print("Navegador configurado!\n")
        except RuntimeError as e:
            raise ScraperError(str(e))

    def human_delay(self, min_sec=2, max_sec=4):
        total = random.uniform(min_sec, max_sec)
        elapsed = 0
        while elapsed < total:
            self._check_stop()
            time.sleep(min(0.5, total - elapsed))
            elapsed += 0.5

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
        self.driver.get('https://www.facebook.com/login')
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

    def _scroll_to_load_all(self):
        """Scroll na pagina de vendas para carregar todos os listings."""
        print("Carregando todos os anuncios...")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        no_change_count = 0

        while no_change_count < SCROLL_STABILIZATION_ATTEMPTS:
            self._check_stop()
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                no_change_count += 1
            else:
                no_change_count = 0
            last_height = new_height

    def _collect_listing_links(self):
        """Coleta links de todos os anuncios visiveis na pagina de vendas."""
        links = []
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/marketplace/item/"]')
        seen = set()
        for el in elements:
            href = el.get_attribute('href')
            if href and '/marketplace/item/' in href:
                clean = href.split('?')[0]
                if clean not in seen:
                    seen.add(clean)
                    links.append(clean)
        return links

    def _scrape_listing_page(self, url):
        """Scrapa dados de uma pagina individual de anuncio."""
        self.driver.get(url)
        self.human_delay(3, 5)

        data = {
            'titulo': '',
            'preco': 0,
            'descricao': '',
            'categoria': '',
            'condicao': 'Usado - Bom',
            'localizacao': '',
            'link_anuncio': url,
            'data_publicacao': '',
            'image_urls': [],
        }

        # Titulo - usar h1 como seletor principal (mais estavel que classes auto-geradas)
        try:
            h1_elements = self.driver.find_elements(By.TAG_NAME, 'h1')
            for h1 in h1_elements:
                txt = h1.text.strip()
                if 3 < len(txt) < MAX_TITLE_LENGTH:
                    data['titulo'] = txt
                    break
            # Fallback: spans com texto razoavel
            if not data['titulo']:
                spans = self.driver.find_elements(
                    By.XPATH,
                    '//span[string-length(text()) > 5 and string-length(text()) < 200]'
                )
                for s in spans:
                    txt = s.text.strip()
                    if 3 < len(txt) < MAX_TITLE_LENGTH and 'R$' not in txt:
                        data['titulo'] = txt
                        break
        except Exception:
            logger.warning("Nao conseguiu extrair titulo de %s", url)

        # Preco
        try:
            price_elements = self.driver.find_elements(
                By.XPATH,
                '//span[contains(text(), "R$") or contains(text(), "$")]'
            )
            for pe in price_elements:
                txt = pe.text.strip()
                if 'R$' in txt or '$' in txt:
                    price_str = txt.replace('R$', '').replace('$', '')
                    price_str = price_str.replace('.', '').replace(',', '.').strip()
                    try:
                        data['preco'] = float(price_str)
                    except ValueError:
                        pass
                    break
        except Exception:
            logger.warning("Nao conseguiu extrair preco de %s", url)

        # Descricao - busca por blocos de texto longos que nao sao titulo nem preco
        try:
            desc_candidates = self.driver.find_elements(
                By.XPATH,
                '//span[string-length(text()) > 20]'
            )
            for dc in desc_candidates:
                txt = dc.text.strip()
                if txt == data['titulo'] or 'R$' in txt:
                    continue
                if len(txt) > 30:
                    data['descricao'] = txt
                    break
        except Exception:
            logger.warning("Nao conseguiu extrair descricao de %s", url)

        # Localizacao - busca por texto com virgula (padrao "Cidade, Estado")
        try:
            loc_elements = self.driver.find_elements(
                By.XPATH,
                '//span[contains(text(), ",") and string-length(text()) < 80]'
            )
            for le in loc_elements:
                txt = le.text.strip()
                if ',' in txt and len(txt) < 80 and not txt.startswith('R$'):
                    data['localizacao'] = txt
                    break
        except Exception:
            logger.warning("Nao conseguiu extrair localizacao de %s", url)

        # Data de publicacao
        try:
            date_elements = self.driver.find_elements(
                By.XPATH,
                '//span[contains(text(), "Listed") or contains(text(), "Publicado") '
                'or contains(text(), "ago") or contains(text(), "atrás") '
                'or contains(text(), "semana") or contains(text(), "dia") '
                'or contains(text(), "hora") or contains(text(), "minuto")]'
            )
            for de in date_elements:
                txt = de.text.strip().lower()
                if any(w in txt for w in ['listed', 'publicado', 'ago', 'atrás',
                                           'semana', 'dia', 'hora', 'minuto']):
                    data['data_publicacao'] = datetime.now().strftime('%Y-%m-%d')
                    break
        except Exception:
            pass

        if not data['data_publicacao']:
            data['data_publicacao'] = datetime.now().strftime('%Y-%m-%d')

        # Imagens - busca por src contendo CDN do Facebook
        try:
            img_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                'img[src*="scontent"], img[src*="fbcdn"]'
            )
            seen_srcs = set()
            for img in img_elements:
                src = img.get_attribute('src')
                if src and ('scontent' in src or 'fbcdn' in src):
                    # Verificar tamanho real da imagem (ignorar icones/avatares)
                    try:
                        natural_w = self.driver.execute_script(
                            "return arguments[0].naturalWidth || arguments[0].width", img
                        )
                        if natural_w and int(natural_w) < MIN_IMAGE_WIDTH:
                            continue
                    except Exception:
                        pass  # Em caso de erro no JS, incluir a imagem
                    if src not in seen_srcs:
                        seen_srcs.add(src)
                        data['image_urls'].append(src)
        except Exception:
            logger.warning("Nao conseguiu extrair imagens de %s", url)

        # Condicao
        try:
            cond_elements = self.driver.find_elements(
                By.XPATH,
                '//span[contains(text(), "Novo") or contains(text(), "Usado") '
                'or contains(text(), "New") or contains(text(), "Used") '
                'or contains(text(), "Como novo") or contains(text(), "Like new")]'
            )
            for ce in cond_elements:
                txt = ce.text.strip()
                if txt in ['Novo', 'New', 'Usado - Como novo', 'Like new',
                           'Usado - Bom', 'Good', 'Usado - Aceitavel', 'Fair']:
                    data['condicao'] = txt
                    break
        except Exception:
            pass

        data = validate_listing_data(data)
        return data

    def _download_images_to_temp(self, image_urls):
        """Faz download das imagens para pasta temporaria.

        Returns:
            Lista de caminhos locais dos arquivos baixados.
        """
        if not image_urls:
            return []

        import tempfile
        temp_dir = Path(tempfile.mkdtemp(prefix="reposter_import_"))

        downloaded = []
        for idx, url in enumerate(image_urls[:MAX_IMAGES_PER_LISTING]):
            try:
                ext = '.jpg'
                dest = temp_dir / f"{idx:03d}_img{ext}"
                response = urllib.request.urlopen(url, timeout=IMAGE_DOWNLOAD_TIMEOUT)
                with open(str(dest), 'wb') as f:
                    f.write(response.read())
                downloaded.append(str(dest))
            except Exception as e:
                logger.warning("Erro ao baixar imagem %d: %s", idx, e)
                print(f"  Erro ao baixar imagem {idx}: {e}")

        return downloaded

    def run(self):
        """Executa o scraper completo."""
        try:
            print("=" * 60)
            print("IMPORTADOR DE ANUNCIOS - Facebook Marketplace")
            print("=" * 60 + "\n")

            self.setup_driver()

            if not self.check_login():
                return

            # Navegar para pagina de vendas
            print("Acessando seus anuncios...")
            self.driver.get(self.SELLING_URL)
            self.human_delay(3, 5)

            # Scroll para carregar todos
            self._scroll_to_load_all()

            # Coletar links
            links = self._collect_listing_links()
            print(f"\nEncontrados {len(links)} anuncios.\n")

            if not links:
                print("Nenhum anuncio encontrado na sua pagina de vendas.")
                return

            # Buscar links existentes no banco para nao duplicar
            existing_links = set()
            if self.data_manager:
                for listing in self.data_manager.get_all_listings():
                    link = listing.get('link_anuncio', '')
                    if link:
                        existing_links.add(link.split('?')[0])

            # Processar cada anuncio
            for idx, link in enumerate(links, 1):
                self._check_stop()

                if self.progress_callback:
                    self.progress_callback(idx, len(links), f"Anuncio {idx}/{len(links)}")

                # Verificar se ja existe
                if link in existing_links:
                    print(f"[{idx}/{len(links)}] Ja importado, pulando: {link}")
                    self.skipped_count += 1
                    continue

                print(f"\n[{idx}/{len(links)}] Importando...")

                try:
                    data = self._scrape_listing_page(link)

                    if not data['titulo']:
                        print("  Nao conseguiu extrair titulo, pulando.")
                        self.error_count += 1
                        continue

                    print(f"  Titulo: {data['titulo']}")
                    print(f"  Preco: R$ {data['preco']}")
                    print(f"  Imagens: {len(data['image_urls'])}")

                    # Baixar imagens para temp
                    temp_image_paths = self._download_images_to_temp(data['image_urls'])

                    if self.data_manager:
                        listing_data = {
                            'titulo': data['titulo'],
                            'preco': data['preco'],
                            'descricao': data['descricao'],
                            'categoria': data['categoria'],
                            'condicao': data['condicao'],
                            'localizacao': data['localizacao'],
                            'status': 'ativo',
                        }
                        # create_listing gera o UUID e copia as imagens
                        # para a pasta correta usando ImageManager
                        created_id = self.data_manager.create_listing(
                            listing_data, temp_image_paths
                        )

                        # Atualizar link e data
                        self.data_manager.update_link_and_date(
                            created_id, link, data['data_publicacao']
                        )

                    # Limpar temp
                    import shutil
                    for p in temp_image_paths:
                        parent = Path(p).parent
                        if parent.name.startswith("reposter_import_"):
                            shutil.rmtree(str(parent), ignore_errors=True)
                            break

                    self.imported_count += 1
                    print("  Importado com sucesso!")

                except Exception as e:
                    logger.error("Erro ao importar anuncio %s: %s", link, e, exc_info=True)
                    print(f"  Erro ao importar: {e}")
                    self.error_count += 1

                # Delay entre anuncios
                self.human_delay(2, 4)

            print("\n" + "=" * 60)
            print("IMPORTACAO CONCLUIDA!")
            print("=" * 60)
            print(f"Importados: {self.imported_count}")
            print(f"Ja existentes: {self.skipped_count}")
            print(f"Erros: {self.error_count}")
            print("=" * 60 + "\n")

        except ScraperError as e:
            print(f"\n{e}")
        except Exception as e:
            logger.error("Erro inesperado no scraper: %s", e, exc_info=True)
            print(f"\nErro inesperado: {e}")
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    from dotenv import load_dotenv
    from gui.utils.paths import get_env_path, get_data_dir
    load_dotenv(get_env_path())
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(get_data_dir() / 'scraper.log', encoding='utf-8'),
            logging.StreamHandler(),
        ]
    )
    from data_layer.local_data_manager import LocalDataManager
    scraper = MarketplaceScraper(data_manager=LocalDataManager())
    scraper.run()
