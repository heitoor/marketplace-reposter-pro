"""
Listings Frame - Tab 'Meus Anuncios'.
Toolbar + Tabela + Status bar + CRUD completo.
"""

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from gui.utils.theme import COLORS, FONTS
from gui.frames.listing_table import ListingTable
from gui.frames.listing_dialog import ListingDialog


class ListingsFrame(ctk.CTkFrame):
    def __init__(self, master, data_manager=None, on_import=None):
        super().__init__(master, fg_color="transparent")

        self.data_manager = data_manager
        self._on_import = on_import

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # tabela expande

        self._create_toolbar()
        self._create_table()
        self._create_statusbar()

        # Carregar dados iniciais
        self.refresh_table()

    def _create_toolbar(self):
        """Toolbar com botoes e busca."""
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # Novo
        ctk.CTkButton(
            toolbar, text="+ Novo",
            font=FONTS["button_small"],
            fg_color=COLORS["success_green"],
            hover_color=COLORS["success_green_hover"],
            width=100, height=35,
            command=self._on_new,
        ).pack(side="left", padx=(0, 5))

        # Editar
        ctk.CTkButton(
            toolbar, text="Editar",
            font=FONTS["button_small"],
            fg_color=COLORS["accent_blue"],
            hover_color=COLORS["accent_blue_hover"],
            width=90, height=35,
            command=self._on_edit,
        ).pack(side="left", padx=(0, 5))

        # Excluir
        ctk.CTkButton(
            toolbar, text="Excluir",
            font=FONTS["button_small"],
            fg_color=COLORS["danger_red"],
            hover_color=COLORS["danger_red_hover"],
            width=90, height=35,
            command=self._on_delete,
        ).pack(side="left", padx=(0, 15))

        # Importar do Facebook
        self.import_btn = ctk.CTkButton(
            toolbar, text="Importar do Facebook",
            font=FONTS["button_small"],
            fg_color="#4267B2",
            hover_color="#365899",
            width=180, height=35,
            command=self._on_import_click,
        )
        self.import_btn.pack(side="left", padx=(0, 5))

        # Separador visual
        sep = ctk.CTkFrame(toolbar, width=2, height=25, fg_color=COLORS["text_secondary"])
        sep.pack(side="left", padx=(0, 15))

        # Status dropdown + aplicar
        ctk.CTkLabel(toolbar, text="Status:", font=FONTS["label"]).pack(side="left", padx=(0, 5))

        self.status_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["ativo", "pausado", "vendido"],
            font=FONTS["label"],
            fg_color=COLORS["bg_frame"],
            button_color=COLORS["accent_blue"],
            width=120,
        )
        self.status_menu.pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            toolbar, text="Aplicar",
            font=FONTS["button_small"],
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["accent_blue"],
            text_color=COLORS["accent_blue"],
            hover_color=COLORS["bg_frame"],
            width=80, height=35,
            command=self._on_apply_status,
        ).pack(side="left", padx=(0, 15))

        # Busca (lado direito)
        self.search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="Buscar...",
            font=FONTS["label"],
            width=200,
        )
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", self._on_search)

    def _create_table(self):
        """Cria a tabela de anuncios."""
        self.table = ListingTable(self, on_double_click=self._on_edit_by_id)
        self.table.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

    def _create_statusbar(self):
        """Barra de status no rodape."""
        self.statusbar = ctk.CTkLabel(
            self, text="", font=FONTS["status"],
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.statusbar.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))

    def refresh_table(self, search_query=None):
        """Recarrega dados do banco na tabela."""
        if not self.data_manager:
            return

        if search_query:
            listings = self.data_manager.search_listings(search_query)
        else:
            listings = self.data_manager.get_all_listings()

        self.table.set_data(listings)
        self._update_statusbar(listings)

    def _update_statusbar(self, listings):
        """Atualiza contadores na barra de status."""
        total = len(listings)
        ativos = sum(1 for l in listings if l.get("status") == "ativo")
        pausados = sum(1 for l in listings if l.get("status") == "pausado")
        vendidos = sum(1 for l in listings if l.get("status") == "vendido")
        self.statusbar.configure(
            text=f"Total: {total} anuncios | Ativos: {ativos} | Pausados: {pausados} | Vendidos: {vendidos}"
        )

    # === Handlers ===

    def _on_new(self):
        """Abre dialog para novo anuncio."""
        ListingDialog(
            self, title="Novo Anuncio",
            on_save=self._save_new_listing,
        )

    def _on_edit(self):
        """Edita o primeiro anuncio selecionado."""
        selected = self.table.get_selected_ids()
        if not selected:
            return
        self._on_edit_by_id(selected[0])

    def _on_edit_by_id(self, listing_id: str):
        """Abre dialog para editar anuncio especifico."""
        listing = self.data_manager.get_listing(listing_id)
        if not listing:
            return

        ListingDialog(
            self, title="Editar Anuncio",
            listing_data=listing,
            on_save=lambda data, imgs: self._save_edited_listing(listing_id, data, imgs),
        )

    def _on_delete(self):
        """Deleta anuncios selecionados com confirmacao."""
        selected = self.table.get_selected_ids()
        if not selected:
            return

        msg = CTkMessagebox(
            title="Confirmar Exclusao",
            message=f"Deseja excluir {len(selected)} anuncio(s)?\nEsta acao nao pode ser desfeita.",
            icon="warning",
            option_1="Cancelar",
            option_2="Excluir",
        )
        if msg.get() == "Excluir":
            self.data_manager.delete_listings(selected)
            self.refresh_table()

    def _on_apply_status(self):
        """Aplica status selecionado aos anuncios marcados."""
        selected = self.table.get_selected_ids()
        if not selected:
            return

        new_status = self.status_menu.get()
        self.data_manager.update_statuses(selected, new_status)
        self.refresh_table()

    def _on_search(self, event=None):
        """Filtra tabela baseado no texto de busca."""
        query = self.search_entry.get().strip()
        if query:
            self.refresh_table(search_query=query)
        else:
            self.refresh_table()

    def _save_new_listing(self, data: dict, image_paths: list):
        """Salva novo anuncio no banco."""
        self.data_manager.create_listing(data, image_paths)
        self.refresh_table()

    def _save_edited_listing(self, listing_id: str, data: dict, image_paths: list):
        """Salva edicao de anuncio existente."""
        self.data_manager.update_listing(listing_id, data, image_paths)
        self.refresh_table()

    def _on_import_click(self):
        """Inicia importacao de anuncios do Facebook."""
        if self._on_import:
            self._on_import()

    def set_import_running(self, running: bool):
        """Desabilita/habilita botao de importar."""
        self.import_btn.configure(
            state="disabled" if running else "normal",
            text="Importando..." if running else "Importar do Facebook",
        )
