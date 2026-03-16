"""
Header Frame - Branding e indicadores de status
"""

import customtkinter as ctk
from gui.utils.theme import COLORS, FONTS, APP_NAME, APP_SUBTITLE


class HeaderFrame(ctk.CTkFrame):
    def __init__(self, master, on_fb_login=None):
        super().__init__(master, fg_color="transparent")

        self._on_fb_login = on_fb_login

        # Layout: 2 linhas
        self.grid_columnconfigure(0, weight=1)

        # Linha 1: Titulo + Botao Login Facebook
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 0))

        self.title_label = ctk.CTkLabel(
            title_frame,
            text=APP_NAME,
            font=FONTS["title"],
            text_color=COLORS["accent_blue"],
        )
        self.title_label.pack(side="left")

        self.subtitle_label = ctk.CTkLabel(
            title_frame,
            text=f"  {APP_SUBTITLE}",
            font=FONTS["subtitle"],
            text_color=COLORS["text_secondary"],
        )
        self.subtitle_label.pack(side="left", padx=(5, 0), pady=(8, 0))

        # Botao Login Facebook (lado direito do header)
        self.fb_login_btn = ctk.CTkButton(
            title_frame,
            text="Login no Facebook",
            font=FONTS["button"],
            fg_color="#4267B2",
            hover_color="#365899",
            width=220,
            height=42,
            corner_radius=8,
            command=self._handle_fb_login,
        )
        self.fb_login_btn.pack(side="right", padx=(10, 0))

        # Linha 2: Status indicators
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.grid(row=1, column=0, sticky="w", padx=20, pady=(5, 10))

        # Facebook status
        self.fb_dot = ctk.CTkLabel(
            status_frame,
            text="\u25CF",
            font=("Segoe UI", 14),
            text_color=COLORS["status_disconnected"],
        )
        self.fb_dot.pack(side="left")

        self.fb_label = ctk.CTkLabel(
            status_frame,
            text="Facebook: Desconectado",
            font=FONTS["status"],
            text_color=COLORS["text_secondary"],
        )
        self.fb_label.pack(side="left", padx=(3, 20))

        # DB status (local - sempre conectado)
        self.db_dot = ctk.CTkLabel(
            status_frame,
            text="\u25CF",
            font=("Segoe UI", 14),
            text_color=COLORS["status_connected"],
        )
        self.db_dot.pack(side="left")

        self.db_label = ctk.CTkLabel(
            status_frame,
            text="BD: Local",
            font=FONTS["status"],
            text_color=COLORS["text_secondary"],
        )
        self.db_label.pack(side="left", padx=(3, 0))

    def set_fb_status(self, status: str):
        """status: 'connected', 'pending', 'disconnected'"""
        color_map = {
            "connected": COLORS["status_connected"],
            "pending": COLORS["status_pending"],
            "disconnected": COLORS["status_disconnected"],
        }
        text_map = {
            "connected": "Facebook: Conectado",
            "pending": "Facebook: Aguardando login...",
            "disconnected": "Facebook: Desconectado",
        }
        self.fb_dot.configure(text_color=color_map.get(status, COLORS["status_disconnected"]))
        self.fb_label.configure(text=text_map.get(status, "Facebook: Desconectado"))

    def set_db_status(self, status: str):
        """status: 'connected', 'disconnected'"""
        if status == "connected":
            self.db_dot.configure(text_color=COLORS["status_connected"])
            self.db_label.configure(text="BD: Local")
        else:
            self.db_dot.configure(text_color=COLORS["status_disconnected"])
            self.db_label.configure(text="BD: Erro")

    def _handle_fb_login(self):
        if self._on_fb_login:
            self._on_fb_login()

    def set_fb_login_running(self, running: bool):
        """Alterna estado do botao de login."""
        if running:
            self.fb_login_btn.configure(
                state="disabled",
                text="Conectando...",
                fg_color="#2c4a7c",
            )
        else:
            self.fb_login_btn.configure(
                state="normal",
                text="Login no Facebook",
                fg_color="#4267B2",
            )

    def set_fb_login_connected(self):
        """Mostra estado conectado no botao."""
        self.fb_login_btn.configure(
            state="disabled",
            text="Conectado - Importando...",
            fg_color=COLORS["success_green"],
        )
