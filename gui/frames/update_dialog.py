"""
Update Dialog - Notifica o usuario sobre nova versao disponivel.
"""

import webbrowser
import customtkinter as ctk
from gui.utils.theme import COLORS, FONTS
from gui.utils.paths import APP_VERSION


class UpdateDialog(ctk.CTkToplevel):
    """Dialog que informa sobre atualizacao disponivel."""

    def __init__(self, master, update_info: dict):
        super().__init__(master)

        self._download_url = update_info.get("download_url", "")
        new_version = update_info.get("version", "?")
        notes = update_info.get("notes", "")

        self.title("Atualizacao Disponivel")
        self.geometry("460x300")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])

        self.transient(master)
        self.grab_set()

        self._create_widgets(new_version, notes)

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 460) // 2
        y = (self.winfo_screenheight() - 300) // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self, new_version, notes):
        main = ctk.CTkFrame(self, fg_color=COLORS["bg_frame"], corner_radius=12)
        main.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(
            main,
            text="Nova versao disponivel!",
            font=FONTS["dialog_title"],
            text_color=COLORS["accent_blue"],
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            main,
            text=f"Sua versao: v{APP_VERSION}    Nova: v{new_version}",
            font=FONTS["subtitle"],
            text_color=COLORS["text_primary"],
        ).pack(pady=(0, 10))

        if notes:
            ctk.CTkLabel(
                main,
                text=notes,
                font=FONTS["label"],
                text_color=COLORS["text_secondary"],
                wraplength=380,
            ).pack(pady=(0, 10), padx=20)

        ctk.CTkLabel(
            main,
            text="Seus anuncios e configuracoes serao mantidos.",
            font=("Segoe UI", 11),
            text_color=COLORS["text_secondary"],
        ).pack(pady=(0, 15))

        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))

        if self._download_url:
            ctk.CTkButton(
                btn_frame,
                text="Baixar Atualizacao",
                font=FONTS["button"],
                fg_color=COLORS["success_green"],
                hover_color=COLORS["success_green_hover"],
                width=180,
                height=40,
                corner_radius=8,
                command=self._download,
            ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Depois",
            font=FONTS["button"],
            fg_color=COLORS["bg_dark"],
            hover_color=COLORS["bg_frame"],
            width=100,
            height=40,
            corner_radius=8,
            command=self._close,
        ).pack(side="left")

    def _download(self):
        if self._download_url:
            webbrowser.open(self._download_url)
        self._close()

    def _close(self):
        self.grab_release()
        self.destroy()
