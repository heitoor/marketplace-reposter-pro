"""
Testes para marketplace_scraper.py
Testa validacao de dados e logica sem Selenium.
"""

import threading
import pytest
from unittest.mock import MagicMock


class TestValidateListingData:
    """Testa funcao de validacao/sanitizacao de dados."""

    def test_titulo_truncado(self):
        from marketplace_scraper import validate_listing_data, MAX_TITLE_LENGTH
        data = {"titulo": "x" * 500}
        result = validate_listing_data(data)
        assert len(result["titulo"]) == MAX_TITLE_LENGTH

    def test_titulo_preservado(self):
        from marketplace_scraper import validate_listing_data
        data = {"titulo": "iPhone 15 Pro"}
        result = validate_listing_data(data)
        assert result["titulo"] == "iPhone 15 Pro"

    def test_preco_negativo_zerado(self):
        from marketplace_scraper import validate_listing_data
        data = {"preco": -100}
        result = validate_listing_data(data)
        assert result["preco"] == 0

    def test_preco_invalido_zerado(self):
        from marketplace_scraper import validate_listing_data
        data = {"preco": "abc"}
        result = validate_listing_data(data)
        assert result["preco"] == 0

    def test_preco_valido(self):
        from marketplace_scraper import validate_listing_data
        data = {"preco": 1500.50}
        result = validate_listing_data(data)
        assert result["preco"] == 1500.50

    def test_preco_none_zerado(self):
        from marketplace_scraper import validate_listing_data
        data = {"preco": None}
        result = validate_listing_data(data)
        assert result["preco"] == 0

    def test_descricao_truncada(self):
        from marketplace_scraper import validate_listing_data, MAX_DESCRIPTION_LENGTH
        data = {"descricao": "d" * 10000}
        result = validate_listing_data(data)
        assert len(result["descricao"]) == MAX_DESCRIPTION_LENGTH

    def test_localizacao_truncada(self):
        from marketplace_scraper import validate_listing_data, MAX_LOCATION_LENGTH
        data = {"localizacao": "l" * 200}
        result = validate_listing_data(data)
        assert len(result["localizacao"]) == MAX_LOCATION_LENGTH

    def test_link_http_rejeitado(self):
        from marketplace_scraper import validate_listing_data
        data = {"link_anuncio": "http://not-https.com"}
        result = validate_listing_data(data)
        assert result["link_anuncio"] == ""

    def test_link_https_aceito(self):
        from marketplace_scraper import validate_listing_data
        data = {"link_anuncio": "https://facebook.com/item/123"}
        result = validate_listing_data(data)
        assert result["link_anuncio"] == "https://facebook.com/item/123"

    def test_imagens_limitadas(self):
        from marketplace_scraper import validate_listing_data, MAX_IMAGES_PER_LISTING
        data = {"image_urls": [f"https://img{i}.jpg" for i in range(20)]}
        result = validate_listing_data(data)
        assert len(result["image_urls"]) == MAX_IMAGES_PER_LISTING

    def test_dados_vazios(self):
        from marketplace_scraper import validate_listing_data
        data = {}
        result = validate_listing_data(data)
        assert result["titulo"] == ""
        assert result["preco"] == 0
        assert result["descricao"] == ""
        assert result["localizacao"] == ""

    def test_titulo_stripped(self):
        from marketplace_scraper import validate_listing_data
        data = {"titulo": "  iPhone 15  "}
        result = validate_listing_data(data)
        assert result["titulo"] == "iPhone 15"


class TestScraperCheckStop:
    """Testa mecanismo de parada do scraper."""

    def test_check_stop_not_set(self):
        from marketplace_scraper import MarketplaceScraper
        event = threading.Event()
        scraper = MarketplaceScraper(stop_event=event)
        scraper._check_stop()  # Nao deve levantar

    def test_check_stop_set_raises(self):
        from marketplace_scraper import MarketplaceScraper, ScraperError
        event = threading.Event()
        event.set()
        scraper = MarketplaceScraper(stop_event=event)
        with pytest.raises(ScraperError, match="cancelada"):
            scraper._check_stop()

    def test_check_stop_none_event(self):
        from marketplace_scraper import MarketplaceScraper
        scraper = MarketplaceScraper(stop_event=None)
        scraper._check_stop()  # Nao deve levantar


class TestScraperCollectLinks:
    """Testa coleta de links (com mock do driver)."""

    def test_collect_links_dedup(self):
        from marketplace_scraper import MarketplaceScraper
        scraper = MarketplaceScraper()
        scraper.driver = MagicMock()

        # Simula elementos com links duplicados
        el1 = MagicMock()
        el1.get_attribute.return_value = "https://facebook.com/marketplace/item/123?ref=1"
        el2 = MagicMock()
        el2.get_attribute.return_value = "https://facebook.com/marketplace/item/123?ref=2"
        el3 = MagicMock()
        el3.get_attribute.return_value = "https://facebook.com/marketplace/item/456"

        scraper.driver.find_elements.return_value = [el1, el2, el3]

        links = scraper._collect_listing_links()
        assert len(links) == 2  # 123 deduplicado
        assert "https://facebook.com/marketplace/item/123" in links
        assert "https://facebook.com/marketplace/item/456" in links

    def test_collect_links_ignores_non_item(self):
        from marketplace_scraper import MarketplaceScraper
        scraper = MarketplaceScraper()
        scraper.driver = MagicMock()

        el = MagicMock()
        el.get_attribute.return_value = "https://facebook.com/marketplace/categories"

        scraper.driver.find_elements.return_value = [el]
        links = scraper._collect_listing_links()
        assert len(links) == 0

    def test_collect_links_ignores_none_href(self):
        from marketplace_scraper import MarketplaceScraper
        scraper = MarketplaceScraper()
        scraper.driver = MagicMock()

        el = MagicMock()
        el.get_attribute.return_value = None

        scraper.driver.find_elements.return_value = [el]
        links = scraper._collect_listing_links()
        assert len(links) == 0
