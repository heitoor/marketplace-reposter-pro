"""
Controls Frame - Botoes INICIAR, PARAR e Configuracoes
"""

import customtkinter as ctk
from gui.utils.theme import COLORS, FONTS


class ControlsFrame(ctk.CTkFrame):
    def __init__(self, master, on_start=None, on_stop=None, on_settings=None):
        super().__init__(master, fg_color="transparent")

        self._on_start = on_start
        self._on_stop = on_stop
        self._on_settings = on_settings
        self._login_mode = False

        # Layout horizontal
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 10))

        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="INICIAR",
            font=FONTS["button"],
            fg_color=COLORS["success_green"],
            hover_color=COLORS["success_green_hover"],
            width=200,
            height=45,
            command=self._handle_start,
        )
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="PARAR",
            font=FONTS["button"],
            fg_color=COLORS["danger_red"],
            hover_color=COLORS["danger_red_hover"],
            width=200,
            height=45,
            state="disabled",
            command=self._handle_stop,
        )
        self.stop_btn.pack(side="left", padx=(0, 10))

        self.settings_btn = ctk.CTkButton(
            btn_frame,
            text="\u2699  Configuracoes",
            font=FONTS["button_small"],
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["accent_blue"],
            text_color=COLORS["accent_blue"],
            hover_color=COLORS["bg_frame"],
            width=160,
            height=45,
            command=self._handle_settings,
        )
        self.settings_btn.pack(side="right")

    def _handle_start(self):
        if self._login_mode and self._on_start:
            self._on_start()
        elif self._on_start:
            self._on_start()

    def _handle_stop(self):
        if self._on_stop:
            self._on_stop()

    def _handle_settings(self):
        if self._on_settings:
            self._on_settings()

    def set_running_state(self, is_running: bool):
        """Alterna estado dos botoes entre rodando e parado."""
        if is_running:
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.settings_btn.configure(state="disabled")
        else:
            self.start_btn.configure(state="normal", text="INICIAR",
                                     fg_color=COLORS["success_green"],
                                     hover_color=COLORS["success_green_hover"])
            self.stop_btn.configure(state="disabled")
            self.settings_btn.configure(state="normal")
            self._login_mode = False

    def set_login_mode(self, active: bool):
        """Transforma botao START em 'LOGIN CONCLUIDO'."""
        self._login_mode = active
        if active:
            self.start_btn.configure(
                state="normal",
                text="LOGIN CONCLUIDO",
                fg_color=COLORS["accent_blue"],
                hover_color=COLORS["accent_blue_hover"],
            )
        else:
            self.start_btn.configure(
                state="disabled",
                text="INICIAR",
                fg_color=COLORS["success_green"],
                hover_color=COLORS["success_green_hover"],
            )
            self._login_mode = False
