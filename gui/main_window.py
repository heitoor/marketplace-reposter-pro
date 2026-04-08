"""
Main Window - Janela principal com abas (CTkTabview).
Aba 'Meus Anuncios' + Aba 'Repostagem'
"""

import queue
import threading

import customtkinter as ctk

from gui.frames.header_frame import HeaderFrame
from gui.frames.repostagem_frame import RepostagemFrame
from gui.frames.listings_frame import ListingsFrame
from gui.frames.login_dialog import LoginDialog
from gui.frames.update_dialog import UpdateDialog
from gui.workers.reposter_worker import ReposterWorker
from gui.workers.scraper_worker import ScraperWorker
from gui.utils.settings_manager import SettingsManager
from gui.utils.theme import COLORS, FONTS, WINDOW_SIZE, WINDOW_MIN_SIZE
from gui.utils.updater import check_for_updates

from data_layer.local_data_manager import LocalDataManager


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("EITO LABS - Marketplace Reposter Pro")
        self.geometry(WINDOW_SIZE)
        self.minsize(*WINDOW_MIN_SIZE)
        self.configure(fg_color=COLORS["bg_dark"])

        # Data manager compartilhado (GUI + Worker)
        self.data_manager = LocalDataManager()

        # Estado interno
        self.message_queue = None
        self.stop_event = None
        self.worker = None
        self.worker_thread = None
        self._is_running = False
        self._active_mode = None  # "repost" ou "import"

        self._create_widgets()
        self._load_initial_settings()
        self._check_updates()

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_widgets(self):
        """Cria header + tabview com 2 abas."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # tabview expande

        # Header
        self.header_frame = HeaderFrame(self, on_fb_login=self._on_fb_login)
        self.header_frame.grid(row=0, column=0, sticky="ew")

        # Tabview
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLORS["bg_dark"],
            segmented_button_fg_color=COLORS["bg_frame"],
            segmented_button_selected_color=COLORS["accent_blue"],
            segmented_button_selected_hover_color=COLORS["accent_blue_hover"],
            segmented_button_unselected_color=COLORS["bg_frame"],
            segmented_button_unselected_hover_color=COLORS["bg_frame"],
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        # Tab: Meus Anuncios
        tab_listings = self.tabview.add("Meus Anuncios")
        tab_listings.grid_columnconfigure(0, weight=1)
        tab_listings.grid_rowconfigure(0, weight=1)

        self.listings_frame = ListingsFrame(
            tab_listings,
            data_manager=self.data_manager,
            on_import=self._on_import,
        )
        self.listings_frame.grid(row=0, column=0, sticky="nsew")

        # Tab: Repostagem
        tab_repostagem = self.tabview.add("Repostagem")
        tab_repostagem.grid_columnconfigure(0, weight=1)
        tab_repostagem.grid_rowconfigure(0, weight=1)

        self.repostagem_frame = RepostagemFrame(
            tab_repostagem,
            on_start=self._on_start,
            on_stop=self._on_stop,
        )
        self.repostagem_frame.grid(row=0, column=0, sticky="nsew")

    def _load_initial_settings(self):
        """Carrega configuracoes do .env."""
        settings = SettingsManager.load()
        self.repostagem_frame.settings_frame.load_settings(settings)

    # ===== Repostagem =====

    def _on_start(self):
        """Handler do botao INICIAR / LOGIN CONCLUIDO."""
        # Se esta em modo login, confirmar login
        if self.worker and hasattr(self.worker, '_login_event'):
            if not self.worker._login_event.is_set():
                self.worker.confirm_login()
                self.repostagem_frame.controls_frame.set_login_mode(False)
                self.repostagem_frame.controls_frame.set_running_state(True)
                self.header_frame.set_fb_status("connected")
                return

        if self._is_running:
            return

        # Validar settings
        is_valid, error = self.repostagem_frame.settings_frame.validate()
        if not is_valid:
            self.repostagem_frame.log_frame.append_log(f"ERRO: {error}")
            return

        # Iniciar worker
        settings = self.repostagem_frame.settings_frame.get_settings()
        self._start_worker(ReposterWorker, settings, mode="repost")

        self.repostagem_frame.controls_frame.set_running_state(True)
        self.repostagem_frame.progress_frame.set_indeterminate("Iniciando...")
        self.repostagem_frame.log_frame.clear_log()
        self.repostagem_frame.log_frame.append_log("Iniciando Marketplace Reposter...")
        self.header_frame.set_fb_status("pending")

    def _on_stop(self):
        """Handler do botao PARAR."""
        if self.stop_event:
            self.stop_event.set()
        self.repostagem_frame.progress_frame.set_indeterminate("Parando...")
        self.repostagem_frame.log_frame.append_log("Solicitando parada...")

    # ===== Login Facebook + Import =====

    def _on_fb_login(self):
        """Handler do botao Login no Facebook (header). Faz login e importa automaticamente."""
        if self._is_running:
            self.repostagem_frame.log_frame.append_log(
                "Aguarde a operacao atual terminar."
            )
            return

        self._start_import(from_header=True)

    # ===== Importacao =====

    def _on_import(self):
        """Handler do botao Importar do Facebook (toolbar listings)."""
        if self._is_running:
            self.repostagem_frame.log_frame.append_log(
                "Aguarde a operacao atual terminar antes de importar."
            )
            return

        self._start_import(from_header=False)

    def _start_import(self, from_header=False):
        """Inicia login + importacao de anuncios."""
        settings = SettingsManager.load()
        self._start_worker(ScraperWorker, settings, mode="import")

        # Mudar para aba Repostagem para ver o log
        self.tabview.set("Repostagem")

        self.listings_frame.set_import_running(True)
        self.header_frame.set_fb_login_running(True)
        self.repostagem_frame.controls_frame.set_running_state(True)
        self.repostagem_frame.progress_frame.set_indeterminate("Conectando ao Facebook...")
        self.repostagem_frame.log_frame.clear_log()
        self.repostagem_frame.log_frame.append_log("Abrindo navegador para login no Facebook...")
        self.repostagem_frame.log_frame.append_log("Apos o login, os anuncios serao importados automaticamente.")
        self.header_frame.set_fb_status("pending")

    # ===== Worker generico =====

    def _start_worker(self, worker_class, settings, mode):
        """Inicia um worker (Reposter ou Scraper)."""
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        self._active_mode = mode

        self.worker = worker_class(
            self.message_queue, self.stop_event, settings,
            data_manager=self.data_manager,
        )

        self.worker_thread = threading.Thread(target=self.worker.run, daemon=True)
        self.worker_thread.start()

        self._is_running = True
        self._poll_queue()

    def _poll_queue(self):
        """Verifica mensagens da fila do worker e atualiza GUI."""
        try:
            while True:
                message = self.message_queue.get_nowait()
                self._dispatch_message(message)
        except queue.Empty:
            pass

        if self.worker_thread and not self.worker_thread.is_alive() and self._is_running:
            self._handle_finished({"success": False, "reposted": 0, "errors": 0})
            return

        if self._is_running:
            self.after(100, self._poll_queue)

    def _dispatch_message(self, message: dict):
        """Roteia mensagem para o handler correto."""
        msg_type = message.get("type")

        if msg_type == "log":
            self.repostagem_frame.log_frame.append_log(message["text"])
        elif msg_type == "progress":
            self.repostagem_frame.progress_frame.update_progress(
                message["current"], message["total"], message["product"]
            )
        elif msg_type == "status":
            if "fb" in message:
                self.header_frame.set_fb_status(message["fb"])
                # Atualizar botao login do header quando conectado
                if message["fb"] == "connected" and self._active_mode == "import":
                    self.header_frame.set_fb_login_connected()
                    self.repostagem_frame.progress_frame.set_indeterminate("Importando anuncios...")
            if "db" in message:
                self.header_frame.set_db_status(message["db"])
        elif msg_type == "login_required":
            self._handle_login_required()
        elif msg_type == "finished":
            self._handle_finished(message)
        elif msg_type == "error":
            self.repostagem_frame.log_frame.append_log(f"ERRO: {message['message']}")

    def _handle_login_required(self):
        """Mostra dialog de instrucoes de login."""
        self.header_frame.set_fb_status("pending")
        self.repostagem_frame.controls_frame.set_login_mode(True)
        self.repostagem_frame.progress_frame.set_indeterminate("Aguardando login no Facebook...")
        self.repostagem_frame.log_frame.append_log(
            "Aguardando login no Facebook..."
        )
        # Atualizar botao do header
        self.header_frame.fb_login_btn.configure(
            text="Aguardando Login...",
            fg_color=COLORS["warning_yellow"],
            state="disabled",
        )
        LoginDialog(self, on_confirm=self._on_login_dialog_confirm)

    def _on_login_dialog_confirm(self):
        """Callback quando usuario confirma login no dialog."""
        if self.worker and hasattr(self.worker, '_login_event'):
            self.worker.confirm_login()
            self.repostagem_frame.controls_frame.set_login_mode(False)
            self.repostagem_frame.controls_frame.set_running_state(True)
            self.header_frame.set_fb_status("connected")
            self.repostagem_frame.log_frame.append_log("Login confirmado!")

            # Atualizar botao do header para mostrar que esta importando
            if self._active_mode == "import":
                self.header_frame.set_fb_login_connected()
                self.repostagem_frame.progress_frame.set_indeterminate("Importando anuncios...")

    def _handle_finished(self, message: dict):
        """Processa finalizacao do worker."""
        self._is_running = False
        self.repostagem_frame.controls_frame.set_running_state(False)

        if self._active_mode == "import":
            self.listings_frame.set_import_running(False)
            if message.get("success"):
                imported = message.get("imported", 0)
                skipped = message.get("skipped", 0)
                errors = message.get("errors", 0)
                self.repostagem_frame.progress_frame.set_indeterminate("Importacao concluida!")
                self.repostagem_frame.log_frame.append_log(
                    f"Concluido! Importados: {imported} | Ja existentes: {skipped} | Erros: {errors}"
                )
                self.repostagem_frame.progress_frame.progress_bar.set(1.0)
            else:
                self.repostagem_frame.progress_frame.reset()
                self.repostagem_frame.log_frame.append_log("Importacao encerrada.")
        else:
            if message.get("success"):
                reposted = message.get("reposted", 0)
                errors = message.get("errors", 0)
                self.repostagem_frame.progress_frame.set_indeterminate("Concluido!")
                self.repostagem_frame.log_frame.append_log(
                    f"Concluido! Repostados: {reposted} | Erros: {errors}"
                )
                self.repostagem_frame.progress_frame.progress_bar.set(1.0)
            else:
                self.repostagem_frame.progress_frame.reset()
                if not message.get("reposted") and not message.get("errors"):
                    self.repostagem_frame.log_frame.append_log("Operacao encerrada.")

        if message.get("success"):
            self.header_frame.set_fb_status("connected")
        else:
            self.header_frame.set_fb_status("disconnected")
        self.header_frame.set_fb_login_running(False)

        # Atualizar tabela de listings
        if self.listings_frame:
            self.listings_frame.refresh_table()

        self.worker = None
        self.worker_thread = None
        self._active_mode = None

    def _check_updates(self):
        """Verifica se ha atualizacao disponivel em background."""
        def _on_update_result(update_info):
            # callback vem de thread de background, usar after() para thread-safety
            if update_info:
                self.after(0, lambda info=update_info: UpdateDialog(self, info))

        check_for_updates(_on_update_result)

    def _on_closing(self):
        """Handler de fechamento da janela."""
        if self.worker_thread and self.worker_thread.is_alive():
            self.stop_event.set()
            self.repostagem_frame.log_frame.append_log("Encerrando... aguarde.")
            self.worker_thread.join(timeout=5)
        self.destroy()
