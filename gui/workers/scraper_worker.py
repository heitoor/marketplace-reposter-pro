"""
Scraper Worker - Thread que importa anuncios do Facebook Marketplace.
Mesmo padrao do ReposterWorker: comunica via queue de mensagens.
"""

import os
import sys
import queue
import threading

from gui.utils.log_redirector import ThreadAwareQueueWriter


class ScraperWorker:
    """Worker que roda MarketplaceScraper em thread separada."""

    def __init__(self, message_queue: queue.Queue, stop_event: threading.Event,
                 settings: dict, data_manager=None):
        self.queue = message_queue
        self.stop_event = stop_event
        self.settings = settings
        self.data_manager = data_manager
        self._login_event = threading.Event()

    def run(self):
        """Entry point da thread worker."""
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        thread_id = threading.current_thread().ident

        sys.stdout = ThreadAwareQueueWriter(self.queue, original_stdout, thread_id)
        sys.stderr = ThreadAwareQueueWriter(self.queue, original_stderr, thread_id)

        try:
            self._apply_settings()

            from marketplace_scraper import MarketplaceScraper

            scraper = MarketplaceScraper(
                data_manager=self.data_manager,
                login_callback=self._wait_for_login,
                stop_event=self.stop_event,
                progress_callback=self._on_progress,
            )

            self.queue.put({"type": "status", "db": "connected"})
            scraper.run()

            self.queue.put({
                "type": "finished",
                "success": True,
                "imported": scraper.imported_count,
                "skipped": scraper.skipped_count,
                "errors": scraper.error_count,
            })

        except Exception as e:
            error_type = type(e).__name__
            self.queue.put({"type": "error", "message": f"[{error_type}] {str(e)}"})
            self.queue.put({
                "type": "finished",
                "success": False,
                "imported": 0,
                "skipped": 0,
                "errors": 0,
            })

        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    def _wait_for_login(self):
        """Bloqueia worker ate GUI confirmar login."""
        self._login_event.clear()
        self.queue.put({"type": "login_required"})
        self._login_event.wait()
        self.queue.put({"type": "status", "fb": "connected"})

    def confirm_login(self):
        """Chamado pela GUI quando usuario confirma login."""
        self._login_event.set()

    def _on_progress(self, current, total, product_name):
        self.queue.put({
            "type": "progress",
            "current": current,
            "total": total,
            "product": product_name,
        })

    def _apply_settings(self):
        os.environ["MIN_DELAY"] = str(self.settings.get("min_delay", 3))
        os.environ["MAX_DELAY"] = str(self.settings.get("max_delay", 8))
        os.environ["HEADLESS"] = str(self.settings.get("headless", False))
