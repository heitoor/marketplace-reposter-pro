"""
Log Frame - Display de log em tempo real
"""

from datetime import datetime
import customtkinter as ctk
from gui.utils.theme import COLORS, FONTS


class LogFrame(ctk.CTkFrame):
    MAX_LINES = 2000

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.textbox = ctk.CTkTextbox(
            self,
            font=FONTS["log"],
            fg_color=COLORS["log_bg"],
            text_color=COLORS["text_log"],
            wrap="word",
            state="disabled",
            corner_radius=8,
        )
        self.textbox.grid(row=0, column=0, sticky="nsew", padx=20, pady=(5, 15))

        self._line_count = 0

    def append_log(self, text: str):
        """Adiciona texto ao log com timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {text}\n"

        self.textbox.configure(state="normal")
        self.textbox.insert("end", line)
        self._line_count += 1

        # Trim se exceder limite
        if self._line_count > self.MAX_LINES:
            self.textbox.delete("1.0", f"{self._line_count - self.MAX_LINES}.0")
            self._line_count = self.MAX_LINES

        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear_log(self):
        """Limpa todo o log."""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
        self._line_count = 0
