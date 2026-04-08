"""
Testes para marketplace_reposter.py
Testa logica de negocio sem precisar de Selenium (mock do WebDriver).
"""

import os
import threading
import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestReposterRetryDecorator:
    """Testa o decorator @retry."""

    def test_retry_succeeds_on_first_attempt(self, mock_app_dirs):
        from marketplace_reposter import retry
        from selenium.common.exceptions import TimeoutException

        call_count = 0

        @retry(max_attempts=3, base_delay=0.01)
        def always_works():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert always_works() == "ok"
        assert call_count == 1

    def test_retry_succeeds_on_second_attempt(self, mock_app_dirs):
        from marketplace_reposter import retry
        from selenium.common.exceptions import TimeoutException

        call_count = 0

        @retry(max_attempts=3, base_delay=0.01)
        def fails_once():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutException()
            return "recovered"

        assert fails_once() == "recovered"
        assert call_count == 2

    def test_retry_exhausted_raises(self, mock_app_dirs):
        from marketplace_reposter import retry
        from selenium.common.exceptions import TimeoutException

        @retry(max_attempts=3, base_delay=0.01)
        def always_fails():
            raise TimeoutException("timeout!")

        with pytest.raises(TimeoutException):
            always_fails()

    def test_retry_non_selenium_exception_not_caught(self, mock_app_dirs):
        from marketplace_reposter import retry

        @retry(max_attempts=3, base_delay=0.01)
        def raises_value_error():
            raise ValueError("not selenium")

        with pytest.raises(ValueError):
            raises_value_error()


class TestReposterXPathEscape:
    """Testa _xpath_escape para prevencao de injection."""

    def test_simple_text(self, mock_app_dirs):
        from marketplace_reposter import MarketplaceReposter
        assert MarketplaceReposter._xpath_escape("hello") == "'hello'"

    def test_text_with_single_quotes(self, mock_app_dirs):
        from marketplace_reposter import MarketplaceReposter
        result = MarketplaceReposter._xpath_escape("it's a test")
        assert result == '"it\'s a test"'

    def test_text_with_double_quotes(self, mock_app_dirs):
        from marketplace_reposter import MarketplaceReposter
        result = MarketplaceReposter._xpath_escape('say "hello"')
        assert result == "'say \"hello\"'"

    def test_text_with_both_quotes(self, mock_app_dirs):
        from marketplace_reposter import MarketplaceReposter
        result = MarketplaceReposter._xpath_escape("it's \"tricky\"")
        assert "concat(" in result


class TestReposterCheckStop:
    """Testa mecanismo de parada."""

    def test_check_stop_no_event(self, mock_app_dirs):
        from marketplace_reposter import MarketplaceReposter
        reposter = MarketplaceReposter(data_manager=MagicMock())
        reposter._check_stop()  # Nao deve levantar

    def test_check_stop_not_set(self, mock_app_dirs):
        from marketplace_reposter import MarketplaceReposter
        event = threading.Event()
        reposter = MarketplaceReposter(data_manager=MagicMock(), stop_event=event)
        reposter._check_stop()  # Nao deve levantar

    def test_check_stop_set_raises(self, mock_app_dirs):
        from marketplace_reposter import MarketplaceReposter, ReposterError
        event = threading.Event()
        event.set()
        reposter = MarketplaceReposter(data_manager=MagicMock(), stop_event=event)
        with pytest.raises(ReposterError, match="cancelada"):
            reposter._check_stop()


class TestReposterHumanDelay:
    """Testa delay humanizado."""

    def test_human_delay_respects_bounds(self, mock_app_dirs):
        from marketplace_reposter import MarketplaceReposter
        reposter = MarketplaceReposter(data_manager=MagicMock())
        start = time.time()
        reposter.human_delay(0.1, 0.2)
        elapsed = time.time() - start
        assert 0.1 <= elapsed < 1.0  # Margem para overhead

    def test_human_delay_interruptible(self, mock_app_dirs):
        from marketplace_reposter import MarketplaceReposter, ReposterError
        event = threading.Event()
        reposter = MarketplaceReposter(data_manager=MagicMock(), stop_event=event)

        def set_after():
            time.sleep(0.2)
            event.set()

        threading.Thread(target=set_after, daemon=True).start()

        with pytest.raises(ReposterError):
            reposter.human_delay(10, 20)  # Seria 10+ segundos, mas interrompido


class TestReposterProcessarProdutos:
    """Testa fluxo de processamento de produtos."""

    def test_sem_produtos(self, mock_app_dirs, capsys):
        from marketplace_reposter import MarketplaceReposter
        dm = MagicMock()
        dm.get_produtos_para_repostar.return_value = []
        reposter = MarketplaceReposter(data_manager=dm)
        reposter.processar_produtos()
        assert reposter.produtos_repostados == 0

    def test_produto_sem_imagens_pula(self, mock_app_dirs):
        from marketplace_reposter import MarketplaceReposter
        dm = MagicMock()
        dm.get_produtos_para_repostar.return_value = [
            {"id": "1", "Título": "Test", "Link Anúncio Atual": ""}
        ]
        dm.get_imagens.return_value = []
        dm.limpar_temp_images.return_value = None

        reposter = MarketplaceReposter(data_manager=dm)
        reposter.driver = MagicMock()
        reposter.wait = MagicMock()
        reposter.processar_produtos()

        assert reposter.produtos_erro == 1
        assert reposter.produtos_repostados == 0

    def test_progress_callback_chamado(self, mock_app_dirs):
        from marketplace_reposter import MarketplaceReposter
        dm = MagicMock()
        dm.get_produtos_para_repostar.return_value = [
            {"id": "1", "Título": "Prod A", "Link Anúncio Atual": ""}
        ]
        dm.get_imagens.return_value = []
        dm.limpar_temp_images.return_value = None

        callback = MagicMock()
        reposter = MarketplaceReposter(
            data_manager=dm, progress_callback=callback
        )
        reposter.driver = MagicMock()
        reposter.wait = MagicMock()
        reposter.processar_produtos()

        callback.assert_called_once_with(1, 1, "Prod A")


class TestReposterRemoverAnuncio:
    """Testa remocao de anuncio."""

    def test_sem_link_retorna_true(self, mock_app_dirs):
        from marketplace_reposter import MarketplaceReposter
        reposter = MarketplaceReposter(data_manager=MagicMock())
        reposter.driver = MagicMock()
        reposter.wait = MagicMock()
        assert reposter.remover_anuncio_antigo("") is True
        assert reposter.remover_anuncio_antigo(None) is True
        assert reposter.remover_anuncio_antigo("   ") is True

    def test_link_invalido_nao_crasheia(self, mock_app_dirs):
        from marketplace_reposter import MarketplaceReposter
        reposter = MarketplaceReposter(data_manager=MagicMock())
        reposter.driver = MagicMock()
        reposter.driver.get.side_effect = Exception("network error")
        reposter.wait = MagicMock()

        # Override human_delay para nao esperar
        reposter.human_delay = MagicMock()

        result = reposter.remover_anuncio_antigo("https://bad-link.com")
        assert result is False
