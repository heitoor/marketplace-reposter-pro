"""
Update Dialog - Notifica sobre nova versao e aplica atualizacao automaticamente.

Fluxo:
1. Mostra info da nova versao
2. Usuario clica "Atualizar Agora"
3. Barra de progresso mostra download
4. Ao concluir, executa instalador silencioso e fecha o app
"""

import threading
import logging

import customtkinter as ctk
from gui.utils.theme import COLORS, FONTS
from gui.utils.paths import APP_VERSION

logger = logging.getLogger(__name__)


class UpdateDialog(ctk.CTkToplevel):
    """Dialog de atualizacao com download automatico."""

    def __init__(self, master, update_info: dict):
        super().__init__(master)

        self._master = master
        self._download_url = update_info.get("download_url", "")
        self._new_version = update_info.get("version", "?")
        self._notes = update_info.get("notes", "")
        self._is_downloading = False

        self.title("Atualizacao Disponivel")
        self.geometry("500x340")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])

        self.transient(master)
        self.grab_set()

        self._create_widgets()

        # Centralizar na tela
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 340) // 2
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self._on_close_attempt)

    def _create_widgets(self):
        self.main_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_frame"], corner_radius=12)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Titulo
        ctk.CTkLabel(
            self.main_frame,
            text="Nova versao disponivel!",
            font=FONTS["dialog_title"],
            text_color=COLORS["accent_blue"],
        ).pack(pady=(20, 10))

        # Versoes
        ctk.CTkLabel(
            self.main_frame,
            text=f"Sua versao: v{APP_VERSION}    Nova: v{self._new_version}",
            font=FONTS["subtitle"],
            text_color=COLORS["text_primary"],
        ).pack(pady=(0, 10))

        # Notas
        if self._notes:
            ctk.CTkLabel(
                self.main_frame,
                text=self._notes,
                font=FONTS["label"],
                text_color=COLORS["text_secondary"],
                wraplength=420,
            ).pack(pady=(0, 5), padx=20)

        # Info de seguranca
        ctk.CTkLabel(
            self.main_frame,
            text="Seus anuncios e configuracoes serao mantidos.",
            font=("Segoe UI", 11),
            text_color=COLORS["text_secondary"],
        ).pack(pady=(0, 10))

        # Status / Progresso
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=FONTS["status"],
            text_color=COLORS["text_secondary"],
        )
        self.status_label.pack(pady=(0, 5))

        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            width=400,
            height=12,
            fg_color=COLORS["bg_dark"],
            progress_color=COLORS["accent_blue"],
        )
        self.progress_bar.pack(pady=(0, 15))
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # Esconder ate clicar

        # Botoes
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.pack(pady=(0, 20))

        if self._download_url:
            self.update_btn = ctk.CTkButton(
                self.btn_frame,
                text="Atualizar Agora",
                font=FONTS["button"],
                fg_color=COLORS["success_green"],
                hover_color=COLORS["success_green_hover"],
                width=180,
                height=40,
                corner_radius=8,
                command=self._start_download,
            )
            self.update_btn.pack(side="left", padx=(0, 10))

        self.later_btn = ctk.CTkButton(
            self.btn_frame,
            text="Depois",
            font=FONTS["button"],
            fg_color=COLORS["bg_dark"],
            hover_color=COLORS["bg_frame"],
            width=100,
            height=40,
            corner_radius=8,
            command=self._close,
        )
        self.later_btn.pack(side="left")

    def _start_download(self):
        """Inicia download do instalador em background."""
        if self._is_downloading:
            return

        self._is_downloading = True

        # Mudar UI para modo download
        self.update_btn.configure(
            text="Baixando...",
            state="disabled",
            fg_color=COLORS["accent_blue"],
        )
        self.later_btn.configure(state="disabled")
        self.progress_bar.pack(before=self.btn_frame, pady=(0, 15))
        self.progress_bar.set(0)
        self.status_label.configure(text="Baixando atualizacao...")

        # Download em thread separada
        thread = threading.Thread(target=self._do_download, daemon=True)
        thread.start()

    def _do_download(self):
        """Executa download (roda em thread de background)."""
        try:
            from gui.utils.updater import download_update, apply_update

            def on_progress(downloaded, total):
                if total > 0:
                    pct = downloaded / total
                    mb_down = downloaded / (1024 * 1024)
                    mb_total = total / (1024 * 1024)
                    self.after(0, lambda p=pct, d=mb_down, t=mb_total: self._update_progress(p, d, t))
                else:
                    mb_down = downloaded / (1024 * 1024)
                    self.after(0, lambda d=mb_down: self._update_progress_unknown(d))

            installer_path = download_update(self._download_url, progress_callback=on_progress)

            # Download concluido - aplicar
            self.after(0, lambda p=installer_path: self._on_download_complete(p))

        except Exception as e:
            logger.error("Erro no download da atualizacao: %s", e, exc_info=True)
            self.after(0, lambda err=str(e): self._on_download_error(err))

    def _update_progress(self, pct: float, mb_downloaded: float, mb_total: float):
        """Atualiza barra de progresso (chamado na main thread)."""
        self.progress_bar.set(pct)
        self.status_label.configure(
            text=f"Baixando... {mb_downloaded:.1f} / {mb_total:.1f} MB ({pct * 100:.0f}%)"
        )

    def _update_progress_unknown(self, mb_downloaded: float):
        """Atualiza progresso quando tamanho total e desconhecido."""
        self.status_label.configure(text=f"Baixando... {mb_downloaded:.1f} MB")

    def _on_download_complete(self, installer_path: str):
        """Download concluido - aplicar atualizacao."""
        self.progress_bar.set(1.0)
        self.status_label.configure(
            text="Download concluido! Instalando...",
            text_color=COLORS["success_green"],
        )
        self.update_btn.configure(text="Instalando...")

        logger.info("Download concluido, aplicando: %s", installer_path)

        # Pequeno delay para o usuario ver a mensagem, depois aplicar
        self.after(1000, lambda: self._apply(installer_path))

    def _apply(self, installer_path: str):
        """Aplica a atualizacao (fecha o app)."""
        from gui.utils.updater import apply_update
        apply_update(installer_path)

    def _on_download_error(self, error_msg: str):
        """Trata erro no download."""
        self._is_downloading = False
        self.progress_bar.pack_forget()
        self.status_label.configure(
            text=f"Erro no download: {error_msg}",
            text_color=COLORS["danger_red"],
        )
        self.update_btn.configure(
            text="Tentar Novamente",
            state="normal",
            fg_color=COLORS["success_green"],
        )
        self.later_btn.configure(state="normal")

    def _on_close_attempt(self):
        """Impede fechar durante download."""
        if self._is_downloading:
            return  # Nao fechar durante download
        self._close()

    def _close(self):
        self.grab_release()
        self.destroy()
