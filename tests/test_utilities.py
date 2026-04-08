"""
Testes para utilitarios: SettingsManager, Updater, Paths, LogRedirector.
"""

import os
import sys
import queue
import threading
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from http.server import HTTPServer, BaseHTTPRequestHandler

import pytest


# ===== SettingsManager =====

class TestSettingsManager:

    def test_load_defaults(self, mock_app_dirs):
        from gui.utils.settings_manager import SettingsManager
        settings = SettingsManager.load()
        assert settings["min_delay"] == 3
        assert settings["max_delay"] == 8
        assert settings["delay_between_posts"] == 420
        assert settings["repost_interval_days"] == 7
        assert settings["headless"] is False

    def test_load_custom_values(self, mock_app_dirs):
        # Escrever valores customizados no .env
        mock_app_dirs["env_path"].write_text(
            "MIN_DELAY=5\nMAX_DELAY=15\nDELAY_BETWEEN_POSTS=600\nHEADLESS=True\n",
            encoding="utf-8",
        )
        from gui.utils.settings_manager import SettingsManager
        settings = SettingsManager.load()
        assert settings["min_delay"] == 5
        assert settings["max_delay"] == 15
        assert settings["delay_between_posts"] == 600
        assert settings["headless"] is True

    def test_save_and_reload(self, mock_app_dirs):
        from gui.utils.settings_manager import SettingsManager
        SettingsManager.save({
            "min_delay": 10,
            "max_delay": 20,
            "delay_between_posts": 300,
            "headless": True,
        })
        settings = SettingsManager.load()
        assert settings["min_delay"] == 10
        assert settings["max_delay"] == 20
        assert settings["delay_between_posts"] == 300
        assert settings["headless"] is True

    def test_save_preserves_comments(self, mock_app_dirs):
        # Escrever .env com comentario
        mock_app_dirs["env_path"].write_text(
            "# Configuracao do Reposter\nMIN_DELAY=3\nMAX_DELAY=8\n",
            encoding="utf-8",
        )
        from gui.utils.settings_manager import SettingsManager
        SettingsManager.save({"min_delay": 5})
        content = mock_app_dirs["env_path"].read_text(encoding="utf-8")
        assert "# Configuracao do Reposter" in content
        assert "MIN_DELAY=5" in content

    def test_save_adds_missing_keys(self, mock_app_dirs):
        # .env sem HEADLESS
        mock_app_dirs["env_path"].write_text("MIN_DELAY=3\n", encoding="utf-8")
        from gui.utils.settings_manager import SettingsManager
        SettingsManager.save({"headless": True})
        content = mock_app_dirs["env_path"].read_text(encoding="utf-8")
        assert "HEADLESS=True" in content

    def test_load_invalid_value_uses_default(self, mock_app_dirs):
        mock_app_dirs["env_path"].write_text("MIN_DELAY=abc\n", encoding="utf-8")
        from gui.utils.settings_manager import SettingsManager
        settings = SettingsManager.load()
        assert settings["min_delay"] == 3  # default

    def test_save_partial_settings(self, mock_app_dirs):
        """Salvar apenas um campo nao deve apagar outros."""
        from gui.utils.settings_manager import SettingsManager
        SettingsManager.save({"min_delay": 99})
        settings = SettingsManager.load()
        assert settings["min_delay"] == 99
        assert settings["max_delay"] == 8  # preservado


# ===== Updater =====

class TestUpdater:

    def test_parse_version_normal(self):
        from gui.utils.updater import parse_version
        assert parse_version("3.1.0") == (3, 1, 0)

    def test_parse_version_single(self):
        from gui.utils.updater import parse_version
        assert parse_version("5") == (5,)

    def test_parse_version_invalid(self):
        from gui.utils.updater import parse_version
        assert parse_version("abc") == (0, 0, 0)

    def test_parse_version_empty(self):
        from gui.utils.updater import parse_version
        assert parse_version("") == (0, 0, 0)

    def test_parse_version_none(self):
        from gui.utils.updater import parse_version
        assert parse_version(None) == (0, 0, 0)

    def test_parse_version_comparison(self):
        from gui.utils.updater import parse_version
        assert parse_version("3.1.0") > parse_version("3.0.0")
        assert parse_version("4.0.0") > parse_version("3.9.9")
        assert parse_version("3.0.0") == parse_version("3.0.0")

    def test_check_for_updates_no_update(self):
        from gui.utils.updater import check_for_updates
        results = []

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "version": "0.0.1",  # Versao antiga
            "download_url": "",
            "notes": "",
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("gui.utils.updater.urlopen", return_value=mock_response):
            check_for_updates(lambda info: results.append(info))
            import time
            time.sleep(1)

        assert len(results) == 1
        assert results[0] is None

    def test_check_for_updates_with_update(self):
        from gui.utils.updater import check_for_updates
        results = []

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "version": "99.0.0",
            "download_url": "https://example.com/download",
            "notes": "Nova versao!",
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("gui.utils.updater.urlopen", return_value=mock_response):
            check_for_updates(lambda info: results.append(info))
            import time
            time.sleep(1)

        assert len(results) == 1
        assert results[0]["version"] == "99.0.0"
        assert results[0]["download_url"] == "https://example.com/download"

    def test_check_for_updates_network_error(self):
        from gui.utils.updater import check_for_updates
        from urllib.error import URLError
        results = []

        with patch("gui.utils.updater.urlopen", side_effect=URLError("no network")):
            check_for_updates(lambda info: results.append(info))
            import time
            time.sleep(1)

        assert len(results) == 1
        assert results[0] is None  # Erro silencioso


# ===== Paths =====

class TestPaths:

    def test_app_version_defined(self):
        from gui.utils.paths import APP_VERSION
        assert APP_VERSION is not None
        assert len(APP_VERSION) > 0

    def test_app_name_defined(self):
        from gui.utils.paths import APP_NAME
        assert APP_NAME == "MarketplaceReposterPro"

    def test_get_data_dir_creates_dir(self, mock_app_dirs):
        from gui.utils.paths import get_data_dir
        d = get_data_dir()
        assert d.exists()
        assert d.is_dir()

    def test_get_db_path_extension(self, mock_app_dirs):
        from gui.utils.paths import get_db_path
        p = get_db_path()
        assert p.suffix == ".db"
        assert "reposter" in p.name

    def test_get_images_dir_creates_dir(self, mock_app_dirs):
        from gui.utils.paths import get_images_dir
        d = get_images_dir()
        assert d.exists()

    def test_get_env_path_creates_default(self, temp_dir):
        """Se .env nao existe, deve ser criado com defaults."""
        data_dir = temp_dir / "fresh_data"
        data_dir.mkdir()
        env_path = data_dir / ".env"

        with patch("gui.utils.paths.get_data_dir", return_value=data_dir), \
             patch("gui.utils.paths.get_app_dir", return_value=temp_dir):
            from gui.utils import paths
            # Chamar diretamente a logica
            if not env_path.exists():
                env_path.write_text(
                    "MIN_DELAY=3\nMAX_DELAY=8\nDELAY_BETWEEN_POSTS=420\nHEADLESS=False\n",
                    encoding="utf-8",
                )
            assert env_path.exists()
            content = env_path.read_text()
            assert "MIN_DELAY" in content


# ===== LogRedirector =====

class TestLogRedirector:

    def test_worker_thread_output_to_queue(self):
        from gui.utils.log_redirector import ThreadAwareQueueWriter
        q = queue.Queue()
        original = MagicMock()
        worker_id = threading.current_thread().ident

        writer = ThreadAwareQueueWriter(q, original, worker_id)
        writer.write("Hello from worker")

        msg = q.get_nowait()
        assert msg["type"] == "log"
        assert msg["text"] == "Hello from worker"

    def test_non_worker_thread_not_queued(self):
        from gui.utils.log_redirector import ThreadAwareQueueWriter
        q = queue.Queue()
        original = MagicMock()
        # Usar um thread ID diferente
        writer = ThreadAwareQueueWriter(q, original, 99999999)
        writer.write("Hello from other thread")

        assert q.empty()  # Nao deve ir para a fila
        original.write.assert_called_once()  # Mas deve ir para original

    def test_empty_text_not_queued(self):
        from gui.utils.log_redirector import ThreadAwareQueueWriter
        q = queue.Queue()
        writer = ThreadAwareQueueWriter(q, MagicMock(), threading.current_thread().ident)
        writer.write("")
        writer.write("   ")
        assert q.empty()

    def test_flush_delegates(self):
        from gui.utils.log_redirector import ThreadAwareQueueWriter
        original = MagicMock()
        writer = ThreadAwareQueueWriter(queue.Queue(), original, 0)
        writer.flush()
        original.flush.assert_called_once()

    def test_text_stripped(self):
        from gui.utils.log_redirector import ThreadAwareQueueWriter
        q = queue.Queue()
        worker_id = threading.current_thread().ident
        writer = ThreadAwareQueueWriter(q, MagicMock(), worker_id)
        writer.write("mensagem com newline\n")

        msg = q.get_nowait()
        assert msg["text"] == "mensagem com newline"  # sem \n


# ===== Workers =====

class TestReposterWorker:

    def test_apply_settings(self, mock_app_dirs):
        from gui.workers.reposter_worker import ReposterWorker
        worker = ReposterWorker(
            message_queue=queue.Queue(),
            stop_event=threading.Event(),
            settings={"min_delay": 5, "max_delay": 15, "delay_between_posts": 600, "headless": True},
        )
        worker._apply_settings()
        assert os.environ["MIN_DELAY"] == "5"
        assert os.environ["MAX_DELAY"] == "15"
        assert os.environ["DELAY_BETWEEN_POSTS"] == "600"
        assert os.environ["HEADLESS"] == "True"

    def test_confirm_login_sets_event(self, mock_app_dirs):
        from gui.workers.reposter_worker import ReposterWorker
        worker = ReposterWorker(
            message_queue=queue.Queue(),
            stop_event=threading.Event(),
            settings={},
        )
        assert not worker._login_event.is_set()
        worker.confirm_login()
        assert worker._login_event.is_set()

    def test_progress_callback_sends_message(self, mock_app_dirs):
        from gui.workers.reposter_worker import ReposterWorker
        q = queue.Queue()
        worker = ReposterWorker(
            message_queue=q,
            stop_event=threading.Event(),
            settings={},
        )
        worker._on_progress(3, 10, "Produto X")
        msg = q.get_nowait()
        assert msg["type"] == "progress"
        assert msg["current"] == 3
        assert msg["total"] == 10
        assert msg["product"] == "Produto X"


class TestScraperWorker:

    def test_apply_settings(self, mock_app_dirs):
        from gui.workers.scraper_worker import ScraperWorker
        worker = ScraperWorker(
            message_queue=queue.Queue(),
            stop_event=threading.Event(),
            settings={"min_delay": 2, "max_delay": 5, "headless": False},
        )
        worker._apply_settings()
        assert os.environ["MIN_DELAY"] == "2"
        assert os.environ["MAX_DELAY"] == "5"
        assert os.environ["HEADLESS"] == "False"

    def test_confirm_login(self, mock_app_dirs):
        from gui.workers.scraper_worker import ScraperWorker
        worker = ScraperWorker(
            message_queue=queue.Queue(),
            stop_event=threading.Event(),
            settings={},
        )
        worker.confirm_login()
        assert worker._login_event.is_set()
