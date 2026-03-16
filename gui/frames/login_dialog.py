"""
Login Dialog - Janela com instrucoes passo-a-passo para login no Facebook.
Aparece quando o reposter precisa de autenticacao.
"""

import customtkinter as ctk
from gui.utils.theme import COLORS, FONTS


class LoginDialog(ctk.CTkToplevel):
    """Dialog modal com instrucoes de login no Facebook."""

    def __init__(self, master, on_confirm=None):
        super().__init__(master)

        self._on_confirm = on_confirm

        self.title("Login no Facebook")
        self.geometry("520x430")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])

        # Modal behavior
        self.transient(master)
        self.grab_set()

        self._create_widgets()

        # Centraliza na tela
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 520) // 2
        y = (self.winfo_screenheight() - 430) // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        main = ctk.CTkFrame(self, fg_color=COLORS["bg_frame"], corner_radius=12)
        main.pack(fill="both", expand=True, padx=15, pady=15)

        # Titulo
        ctk.CTkLabel(
            main,
            text="Login no Facebook",
            font=FONTS["dialog_title"],
            text_color=COLORS["text_primary"],
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            main,
            text="Uma janela do Chrome foi aberta para voce fazer login.",
            font=FONTS["subtitle"],
            text_color=COLORS["text_secondary"],
        ).pack(pady=(0, 15))

        # Passos
        steps_frame = ctk.CTkFrame(main, fg_color=COLORS["bg_dark"], corner_radius=8)
        steps_frame.pack(fill="x", padx=25, pady=(0, 15))

        steps = [
            ("1", "Acesse a janela do Chrome que abriu automaticamente"),
            ("2", "Digite seu email e senha do Facebook"),
            ("3", "Resolva o CAPTCHA se aparecer"),
            ("4", "Aguarde ate estar completamente logado no Feed"),
            ("5", "Volte aqui e clique no botao abaixo"),
        ]

        for num, text in steps:
            row = ctk.CTkFrame(steps_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=6)

            # Numero em circulo
            ctk.CTkLabel(
                row,
                text=num,
                font=("Segoe UI", 13, "bold"),
                text_color=COLORS["bg_dark"],
                fg_color=COLORS["accent_blue"],
                corner_radius=12,
                width=26,
                height=26,
            ).pack(side="left", padx=(0, 12))

            ctk.CTkLabel(
                row,
                text=text,
                font=FONTS["label"],
                text_color=COLORS["text_primary"],
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

        # Aviso
        ctk.CTkLabel(
            main,
            text="Seus dados ficam salvos localmente. Nao enviamos sua senha.",
            font=("Segoe UI", 11),
            text_color=COLORS["text_secondary"],
        ).pack(pady=(5, 10))

        # Botao confirmar
        self.confirm_btn = ctk.CTkButton(
            main,
            text="JA FIZ LOGIN",
            font=FONTS["button"],
            fg_color=COLORS["success_green"],
            hover_color=COLORS["success_green_hover"],
            width=250,
            height=45,
            corner_radius=8,
            command=self._on_confirm_click,
        )
        self.confirm_btn.pack(pady=(0, 20))

        self.protocol("WM_DELETE_WINDOW", self._on_confirm_click)

    def _on_confirm_click(self):
        if self._on_confirm:
            self._on_confirm()
        self.grab_release()
        self.destroy()
