"""
Settings Frame - Painel de configuracoes colapsavel
"""

import customtkinter as ctk
from gui.utils.theme import COLORS, FONTS
from gui.utils.settings_manager import SettingsManager


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, on_save=None):
        super().__init__(master, fg_color=COLORS["bg_frame"], corner_radius=8)

        self._on_save = on_save
        self._visible = False

        # Container interno com padding
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)

        # Titulo da secao
        title = ctk.CTkLabel(
            inner,
            text="Configuracoes de Automacao",
            font=("Segoe UI", 15, "bold"),
            text_color=COLORS["accent_blue"],
        )
        title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        # Linha 1: Delays
        ctk.CTkLabel(inner, text="Min Delay (s):", font=FONTS["label"]).grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.min_delay_entry = ctk.CTkEntry(inner, width=80, font=FONTS["label"])
        self.min_delay_entry.grid(row=1, column=1, sticky="w", padx=(10, 20), pady=5)

        ctk.CTkLabel(inner, text="Max Delay (s):", font=FONTS["label"]).grid(
            row=1, column=2, sticky="w", pady=5
        )
        self.max_delay_entry = ctk.CTkEntry(inner, width=80, font=FONTS["label"])
        self.max_delay_entry.grid(row=1, column=3, sticky="w", padx=(10, 0), pady=5)

        # Linha 2: Delay entre posts + Headless
        ctk.CTkLabel(inner, text="Delay entre posts (s):", font=FONTS["label"]).grid(
            row=2, column=0, sticky="w", pady=5
        )
        self.delay_posts_entry = ctk.CTkEntry(inner, width=100, font=FONTS["label"])
        self.delay_posts_entry.grid(row=2, column=1, sticky="w", padx=(10, 20), pady=5)

        self.headless_switch = ctk.CTkSwitch(
            inner,
            text="Modo Headless",
            font=FONTS["label"],
            onvalue=True,
            offvalue=False,
        )
        self.headless_switch.grid(row=2, column=2, columnspan=2, sticky="w", pady=5)

        # Linha 3: Botao salvar
        self.save_btn = ctk.CTkButton(
            inner,
            text="Salvar Configuracoes",
            font=FONTS["button_small"],
            fg_color=COLORS["accent_blue"],
            hover_color=COLORS["accent_blue_hover"],
            width=180,
            height=35,
            command=self._save,
        )
        self.save_btn.grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))

        self._status_label = ctk.CTkLabel(
            inner,
            text="",
            font=FONTS["status"],
            text_color=COLORS["success_green"],
        )
        self._status_label.grid(row=3, column=2, columnspan=2, sticky="w", padx=(10, 0), pady=(10, 0))

        # Iniciar oculto
        self.grid_remove()

    def load_settings(self, settings: dict):
        """Popula campos com valores do dict."""
        self.min_delay_entry.delete(0, "end")
        self.min_delay_entry.insert(0, str(settings.get("min_delay", 3)))

        self.max_delay_entry.delete(0, "end")
        self.max_delay_entry.insert(0, str(settings.get("max_delay", 8)))

        self.delay_posts_entry.delete(0, "end")
        self.delay_posts_entry.insert(0, str(settings.get("delay_between_posts", 420)))

        if settings.get("headless", False):
            self.headless_switch.select()
        else:
            self.headless_switch.deselect()

    def get_settings(self) -> dict:
        """Retorna dict com valores atuais dos campos."""
        return {
            "min_delay": self._safe_int(self.min_delay_entry.get(), 3),
            "max_delay": self._safe_int(self.max_delay_entry.get(), 8),
            "delay_between_posts": self._safe_int(self.delay_posts_entry.get(), 420),
            "headless": self.headless_switch.get(),
        }

    def validate(self) -> tuple:
        """Valida configuracoes. Retorna (is_valid, error_message)."""
        settings = self.get_settings()

        if settings["min_delay"] <= 0 or settings["max_delay"] <= 0:
            return False, "Os delays devem ser maiores que 0!"

        if settings["min_delay"] > settings["max_delay"]:
            return False, "Min Delay deve ser menor ou igual ao Max Delay!"

        if settings["delay_between_posts"] <= 0:
            return False, "Delay entre posts deve ser maior que 0!"

        return True, ""

    def toggle(self):
        """Alterna visibilidade do painel."""
        if self._visible:
            self.grid_remove()
        else:
            self.grid()
        self._visible = not self._visible

    def _save(self):
        """Salva configuracoes no .env."""
        is_valid, error = self.validate()
        if not is_valid:
            self._status_label.configure(text=error, text_color=COLORS["danger_red"])
            return

        settings = self.get_settings()
        SettingsManager.save(settings)
        self._status_label.configure(text="Salvo!", text_color=COLORS["success_green"])

        if self._on_save:
            self._on_save(settings)

        self.after(3000, lambda: self._status_label.configure(text=""))

    @staticmethod
    def _safe_int(value: str, default: int) -> int:
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
