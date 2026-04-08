"""
Reposter Worker - Thread que encapsula a automacao do MarketplaceReposter.
Comunica com a GUI via queue de mensagens.
"""

import os
import sys
import queue
import threading

from gui.utils.log_redirector import ThreadAwareQueueWriter

LOGIN_TIMEOUT = 300  # 5 minutos para o usuario fazer login


class ReposterWorker:
    """
    Worker que roda em thread separada.
    Cria e executa o MarketplaceReposter, redirecionando
    toda saida para a fila de mensagens da GUI.
    """

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

            from dotenv import load_dotenv
            from gui.utils.paths import get_env_path
            load_dotenv(get_env_path(), override=True)

            from marketplace_reposter import MarketplaceReposter, ReposterError

            reposter = MarketplaceReposter(
                data_manager=self.data_manager,
                login_callback=self._wait_for_login,
                stop_event=self.stop_event,
                progress_callback=self._on_progress,
            )

            self.queue.put({"type": "status", "db": "connected"})
            reposter.run()

            self.queue.put({
                "type": "finished",
                "success": True,
                "reposted": reposter.produtos_repostados,
                "errors": reposter.produtos_erro,
            })

        except Exception as e:
            error_type = type(e).__name__
            self.queue.put({"type": "error", "message": f"[{error_type}] {str(e)}"})
            self.queue.put({
                "type": "finished",
                "success": False,
                "reposted": 0,
                "errors": 0,
            })

        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    def _wait_for_login(self):
        """Bloqueia worker ate GUI confirmar login (com timeout)."""
        self._login_event.clear()
        self.queue.put({"type": "login_required"})
        logged_in = self._login_event.wait(timeout=LOGIN_TIMEOUT)
        if not logged_in:
            raise TimeoutError(
                f"Timeout de {LOGIN_TIMEOUT}s aguardando login no Facebook."
            )
        self.queue.put({"type": "status", "fb": "connected"})

    def confirm_login(self):
        """Chamado pela GUI quando usuario confirma login."""
        self._login_event.set()

    def _on_progress(self, current, total, product_name):
        """Callback de progresso."""
        self.queue.put({
            "type": "progress",
            "current": current,
            "total": total,
            "product": product_name,
        })

    def _apply_settings(self):
        """Aplica settings no os.environ para o codigo existente usar."""
        os.environ["MIN_DELAY"] = str(self.settings.get("min_delay", 3))
        os.environ["MAX_DELAY"] = str(self.settings.get("max_delay", 8))
        os.environ["DELAY_BETWEEN_POSTS"] = str(self.settings.get("delay_between_posts", 420))
        os.environ["HEADLESS"] = str(self.settings.get("headless", False))
        if "repost_interval_days" in self.settings:
            os.environ["REPOST_INTERVAL_DAYS"] = str(self.settings["repost_interval_days"])
