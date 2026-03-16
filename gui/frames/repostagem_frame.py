"""
Repostagem Frame - Wrapper que contem os frames de controle, progresso, settings e log.
Esta e a aba "Repostagem" do CTkTabview.
"""

import customtkinter as ctk

from gui.frames.controls_frame import ControlsFrame
from gui.frames.progress_frame import ProgressFrame
from gui.frames.settings_frame import SettingsFrame
from gui.frames.log_frame import LogFrame


class RepostagemFrame(ctk.CTkFrame):
    def __init__(self, master, on_start=None, on_stop=None):
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # log expande

        self.controls_frame = ControlsFrame(
            self,
            on_start=on_start,
            on_stop=on_stop,
            on_settings=self._on_settings_toggle,
        )
        self.controls_frame.grid(row=0, column=0, sticky="ew")

        self.progress_frame = ProgressFrame(self)
        self.progress_frame.grid(row=1, column=0, sticky="ew")

        self.settings_frame = SettingsFrame(self, on_save=None)
        self.settings_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 5))
        self.settings_frame.grid_remove()

        self.log_frame = LogFrame(self)
        self.log_frame.grid(row=3, column=0, sticky="nsew")

    def _on_settings_toggle(self):
        self.settings_frame.toggle()
