"""
Listing Table - Tabela scrollavel de anuncios com checkbox, hover e selecao.
"""

import customtkinter as ctk
from gui.utils.theme import COLORS, FONTS


class ListingTable(ctk.CTkFrame):
    """Tabela customizada com header fixo e linhas scrollaveis."""

    COLUMNS = [
        {"key": "titulo", "label": "Titulo", "width": 280},
        {"key": "preco", "label": "Preco (R$)", "width": 100},
        {"key": "status", "label": "Status", "width": 90},
        {"key": "data_publicacao", "label": "Ultima Postagem", "width": 130},
        {"key": "post_count", "label": "Posts", "width": 60},
        {"key": "localizacao", "label": "Localizacao", "width": 180},
    ]

    def __init__(self, master, on_double_click=None):
        super().__init__(master, fg_color="transparent")

        self._on_double_click = on_double_click
        self._rows_data = []
        self._checkboxes = {}
        self._row_frames = {}
        self._select_all_var = ctk.BooleanVar(value=False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self._create_header()

        # Scrollable body
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg_dark"],
            corner_radius=0,
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(1, weight=1)

    def _create_header(self):
        """Cria linha de cabecalho."""
        header = ctk.CTkFrame(self, fg_color=COLORS["table_header_bg"], height=35, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        # Checkbox select all
        self._select_all_cb = ctk.CTkCheckBox(
            header, text="", width=30,
            variable=self._select_all_var,
            command=self._toggle_select_all,
        )
        self._select_all_cb.grid(row=0, column=0, padx=(10, 5), pady=5)

        for i, col in enumerate(self.COLUMNS):
            lbl = ctk.CTkLabel(
                header, text=col["label"],
                font=FONTS["table_header"],
                text_color=COLORS["text_primary"],
                width=col["width"],
                anchor="w",
            )
            lbl.grid(row=0, column=i + 1, padx=(5, 0), pady=5, sticky="w")

    def set_data(self, listings: list):
        """Atualiza tabela com nova lista de anuncios."""
        # Limpar linhas existentes
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self._checkboxes.clear()
        self._row_frames.clear()
        self._rows_data = listings
        self._select_all_var.set(False)

        if not listings:
            self._show_empty_state()
            return

        for idx, listing in enumerate(listings):
            self._create_row(idx, listing)

    def _show_empty_state(self):
        """Mostra mensagem quando nao ha anuncios."""
        empty_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        empty_frame.grid(row=0, column=0, sticky="nsew", pady=60)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            empty_frame,
            text="Nenhum anuncio cadastrado",
            font=("Segoe UI", 16, "bold"),
            text_color=COLORS["text_secondary"],
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            empty_frame,
            text="Clique em '+ Novo' para criar um anuncio\nou 'Importar do Facebook' para importar existentes.",
            font=FONTS["label"],
            text_color=COLORS["text_secondary"],
            justify="center",
        ).pack()

    def _create_row(self, idx: int, listing: dict):
        """Cria uma linha da tabela."""
        bg = COLORS["table_row_bg"] if idx % 2 == 0 else COLORS["table_row_alt_bg"]
        listing_id = listing.get("id", "")

        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color=bg, height=36, corner_radius=0)
        row_frame.grid(row=idx, column=0, columnspan=len(self.COLUMNS) + 1, sticky="ew", pady=(0, 1))
        row_frame.grid_propagate(False)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # Checkbox
        var = ctk.BooleanVar(value=False)
        cb = ctk.CTkCheckBox(row_frame, text="", width=30, variable=var)
        cb.grid(row=0, column=0, padx=(10, 5), pady=4)
        self._checkboxes[listing_id] = var

        # Colunas
        for i, col in enumerate(self.COLUMNS):
            value = listing.get(col["key"], "")

            # Formatar preco
            if col["key"] == "preco" and value:
                try:
                    value = f"{float(value):,.2f}"
                except (ValueError, TypeError):
                    pass

            # Cor do status
            text_color = COLORS["text_primary"]
            if col["key"] == "status":
                status_lower = str(value).lower()
                text_color = COLORS.get(f"status_{status_lower}", COLORS["text_primary"])
                value = str(value).capitalize()

            lbl = ctk.CTkLabel(
                row_frame, text=str(value),
                font=FONTS["table_cell"],
                text_color=text_color,
                width=col["width"],
                anchor="w",
            )
            lbl.grid(row=0, column=i + 1, padx=(5, 0), pady=4, sticky="w")

            # Bind double-click em todos os labels
            lbl.bind("<Double-Button-1>", lambda e, lid=listing_id: self._on_row_double_click(lid))

        # Bind double-click no frame tambem
        row_frame.bind("<Double-Button-1>", lambda e, lid=listing_id: self._on_row_double_click(lid))

        self._row_frames[listing_id] = row_frame

    def _on_row_double_click(self, listing_id: str):
        """Handler de duplo-click numa linha."""
        if self._on_double_click:
            self._on_double_click(listing_id)

    def _toggle_select_all(self):
        """Toggle selecao de todas as linhas."""
        value = self._select_all_var.get()
        for var in self._checkboxes.values():
            var.set(value)

    def get_selected_ids(self) -> list:
        """Retorna lista de IDs selecionados."""
        return [lid for lid, var in self._checkboxes.items() if var.get()]

    def get_row_count(self) -> int:
        return len(self._rows_data)
