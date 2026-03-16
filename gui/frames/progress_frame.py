"""
Progress Frame - Barra de progresso e indicador de produto atual
"""

import customtkinter as ctk
from gui.utils.theme import COLORS, FONTS


class ProgressFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=(0, 5))
        inner.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(
            inner,
            progress_color=COLORS["accent_blue"],
            fg_color=COLORS["bg_frame"],
            height=12,
            corner_radius=6,
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            inner,
            text="Aguardando...",
            font=FONTS["status"],
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.status_label.grid(row=1, column=0, sticky="w")

    def update_progress(self, current: int, total: int, product_name: str):
        """Atualiza barra e texto de progresso."""
        if total > 0:
            self.progress_bar.set(current / total)
        self.status_label.configure(
            text=f"Produto {current}/{total} - {product_name}",
            text_color=COLORS["text_primary"],
        )

    def set_indeterminate(self, message: str):
        """Mostra mensagem sem progresso definido."""
        self.progress_bar.set(0)
        self.status_label.configure(
            text=message,
            text_color=COLORS["warning_yellow"],
        )

    def reset(self):
        """Reseta para estado inicial."""
        self.progress_bar.set(0)
        self.status_label.configure(
            text="Aguardando...",
            text_color=COLORS["text_secondary"],
        )
