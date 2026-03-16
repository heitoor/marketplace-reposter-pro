"""
Listing Dialog - Modal de adicionar/editar anuncio (CTkToplevel).
Suporta campos fixos, imagens com thumbnails e campos personalizados.
"""

import tkinter.filedialog as filedialog
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from gui.utils.theme import COLORS, FONTS


class ListingDialog(ctk.CTkToplevel):
    """Modal para criar ou editar um anuncio."""

    CONDICOES = ["Novo", "Usado - Como novo", "Usado - Bom", "Usado - Aceitavel"]

    def __init__(self, master, title="Novo Anuncio", listing_data=None, on_save=None):
        super().__init__(master)

        self.title(title)
        self.geometry("650x750")
        self.minsize(600, 650)
        self.configure(fg_color=COLORS["bg_dark"])
        self.transient(master)
        self.grab_set()

        self._on_save = on_save
        self._listing_data = listing_data or {}
        self._image_paths = list(self._listing_data.get("images", []))
        self._custom_field_rows = []

        self._create_widgets()
        self._populate_fields()

    def _create_widgets(self):
        """Cria todos os widgets do dialog."""
        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(15, 5))
        scroll.grid_columnconfigure(1, weight=1)

        row = 0

        # === Informacoes Basicas ===
        ctk.CTkLabel(scroll, text="Informacoes Basicas",
                     font=FONTS["section_title"],
                     text_color=COLORS["accent_blue"]).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 10))
        row += 1

        # Titulo
        ctk.CTkLabel(scroll, text="Titulo:", font=FONTS["label"]).grid(
            row=row, column=0, sticky="w", pady=4)
        self.titulo_entry = ctk.CTkEntry(scroll, font=FONTS["label"])
        self.titulo_entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=4)
        row += 1

        # Preco
        ctk.CTkLabel(scroll, text="Preco (R$):", font=FONTS["label"]).grid(
            row=row, column=0, sticky="w", pady=4)
        self.preco_entry = ctk.CTkEntry(scroll, width=150, font=FONTS["label"])
        self.preco_entry.grid(row=row, column=1, sticky="w", padx=(10, 0), pady=4)
        row += 1

        # Categoria
        ctk.CTkLabel(scroll, text="Categoria:", font=FONTS["label"]).grid(
            row=row, column=0, sticky="w", pady=4)
        self.categoria_entry = ctk.CTkEntry(scroll, font=FONTS["label"])
        self.categoria_entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=4)
        row += 1

        # Condicao
        ctk.CTkLabel(scroll, text="Condicao:", font=FONTS["label"]).grid(
            row=row, column=0, sticky="w", pady=4)
        self.condicao_menu = ctk.CTkOptionMenu(
            scroll, values=self.CONDICOES, font=FONTS["label"],
            fg_color=COLORS["bg_frame"],
            button_color=COLORS["accent_blue"],
        )
        self.condicao_menu.grid(row=row, column=1, sticky="w", padx=(10, 0), pady=4)
        row += 1

        # Localizacao
        ctk.CTkLabel(scroll, text="Localizacao:", font=FONTS["label"]).grid(
            row=row, column=0, sticky="w", pady=4)
        self.localizacao_entry = ctk.CTkEntry(scroll, font=FONTS["label"])
        self.localizacao_entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=4)
        row += 1

        # Descricao
        ctk.CTkLabel(scroll, text="Descricao:", font=FONTS["label"]).grid(
            row=row, column=0, sticky="nw", pady=4)
        self.descricao_text = ctk.CTkTextbox(
            scroll, height=100, font=FONTS["label"],
            fg_color=COLORS["bg_frame"],
        )
        self.descricao_text.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=4)
        row += 1

        # === Imagens ===
        ctk.CTkLabel(scroll, text="Imagens",
                     font=FONTS["section_title"],
                     text_color=COLORS["accent_blue"]).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(15, 5))
        row += 1

        self.thumbs_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.thumbs_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        row += 1

        img_btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        img_btn_frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=5)

        ctk.CTkButton(
            img_btn_frame, text="+ Adicionar Imagens",
            font=FONTS["button_small"],
            fg_color=COLORS["accent_blue"],
            hover_color=COLORS["accent_blue_hover"],
            width=160, height=32,
            command=self._add_images,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            img_btn_frame, text="Limpar Imagens",
            font=FONTS["button_small"],
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["danger_red"],
            text_color=COLORS["danger_red"],
            hover_color=COLORS["bg_frame"],
            width=140, height=32,
            command=self._clear_images,
        ).pack(side="left")

        self.img_count_label = ctk.CTkLabel(
            img_btn_frame, text="0 imagens",
            font=FONTS["status"], text_color=COLORS["text_secondary"])
        self.img_count_label.pack(side="left", padx=(15, 0))
        row += 1

        # === Campos Personalizados ===
        ctk.CTkLabel(scroll, text="Campos Personalizados",
                     font=FONTS["section_title"],
                     text_color=COLORS["accent_blue"]).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(15, 5))
        row += 1

        self.custom_fields_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.custom_fields_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        self.custom_fields_frame.grid_columnconfigure(0, weight=1)
        self.custom_fields_frame.grid_columnconfigure(1, weight=1)
        row += 1

        ctk.CTkButton(
            scroll, text="+ Adicionar Campo",
            font=FONTS["button_small"],
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["accent_blue"],
            text_color=COLORS["accent_blue"],
            hover_color=COLORS["bg_frame"],
            width=160, height=32,
            command=self._add_custom_field_row,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=5)
        row += 1

        self._scroll_ref = scroll
        self._next_row = row

        # === Botoes (fixos no fundo) ===
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 15))

        ctk.CTkButton(
            btn_frame, text="Salvar",
            font=FONTS["button"],
            fg_color=COLORS["success_green"],
            hover_color=COLORS["success_green_hover"],
            width=150, height=40,
            command=self._save,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame, text="Cancelar",
            font=FONTS["button"],
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["text_secondary"],
            text_color=COLORS["text_secondary"],
            hover_color=COLORS["bg_frame"],
            width=150, height=40,
            command=self.destroy,
        ).pack(side="left")

    def _populate_fields(self):
        """Preenche campos com dados existentes (modo edicao)."""
        data = self._listing_data
        if not data:
            return

        if data.get("titulo"):
            self.titulo_entry.insert(0, data["titulo"])
        if data.get("preco"):
            self.preco_entry.insert(0, str(data["preco"]))
        if data.get("categoria"):
            self.categoria_entry.insert(0, data["categoria"])
        if data.get("condicao"):
            self.condicao_menu.set(data["condicao"])
        if data.get("localizacao"):
            self.localizacao_entry.insert(0, data["localizacao"])
        if data.get("descricao"):
            self.descricao_text.insert("1.0", data["descricao"])

        # Campos personalizados
        custom = data.get("custom_fields", {})
        for key, value in custom.items():
            self._add_custom_field_row(key, value)

        # Thumbnails
        self._refresh_thumbnails()

    def _add_images(self):
        """Abre file dialog para selecionar imagens."""
        paths = filedialog.askopenfilenames(
            title="Selecionar Imagens",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.bmp *.webp"), ("Todos", "*.*")],
        )
        if paths:
            self._image_paths.extend(paths)
            self._refresh_thumbnails()

    def _clear_images(self):
        """Remove todas as imagens."""
        self._image_paths.clear()
        self._refresh_thumbnails()

    def _refresh_thumbnails(self):
        """Atualiza exibicao de thumbnails."""
        for widget in self.thumbs_frame.winfo_children():
            widget.destroy()

        for i, path in enumerate(self._image_paths[:10]):
            try:
                pil_img = Image.open(path)
                pil_img.thumbnail((70, 70))
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(70, 70))
                lbl = ctk.CTkLabel(self.thumbs_frame, image=ctk_img, text="")
                lbl.grid(row=0, column=i, padx=3, pady=3)
                # Manter referencia para evitar garbage collection
                lbl._ctk_image = ctk_img
            except Exception:
                lbl = ctk.CTkLabel(
                    self.thumbs_frame, text="?",
                    width=70, height=70,
                    fg_color=COLORS["bg_frame"],
                    corner_radius=4,
                )
                lbl.grid(row=0, column=i, padx=3, pady=3)

        count = len(self._image_paths)
        self.img_count_label.configure(text=f"{count} imagem(ns)")

    def _add_custom_field_row(self, key="", value=""):
        """Adiciona linha de campo personalizado."""
        row_idx = len(self._custom_field_rows)

        row_frame = ctk.CTkFrame(self.custom_fields_frame, fg_color="transparent")
        row_frame.grid(row=row_idx, column=0, columnspan=3, sticky="ew", pady=2)

        key_entry = ctk.CTkEntry(row_frame, placeholder_text="Nome do campo",
                                  width=180, font=FONTS["label"])
        key_entry.pack(side="left", padx=(0, 5))
        if key:
            key_entry.insert(0, key)

        value_entry = ctk.CTkEntry(row_frame, placeholder_text="Valor",
                                    width=250, font=FONTS["label"])
        value_entry.pack(side="left", padx=(0, 5))
        if value:
            value_entry.insert(0, value)

        remove_btn = ctk.CTkButton(
            row_frame, text="X", width=30, height=28,
            fg_color=COLORS["danger_red"],
            hover_color=COLORS["danger_red_hover"],
            command=lambda: self._remove_custom_field(row_frame, key_entry, value_entry),
        )
        remove_btn.pack(side="left")

        self._custom_field_rows.append((row_frame, key_entry, value_entry))

    def _remove_custom_field(self, frame, key_entry, value_entry):
        """Remove linha de campo personalizado."""
        frame.destroy()
        self._custom_field_rows = [
            (f, k, v) for f, k, v in self._custom_field_rows if f != frame
        ]

    def _get_custom_fields(self) -> dict:
        """Retorna dict dos campos personalizados."""
        fields = {}
        for _, key_entry, value_entry in self._custom_field_rows:
            key = key_entry.get().strip()
            value = value_entry.get().strip()
            if key:
                fields[key] = value
        return fields

    def _save(self):
        """Valida e salva o anuncio."""
        titulo = self.titulo_entry.get().strip()
        if not titulo:
            self.titulo_entry.configure(border_color=COLORS["danger_red"])
            return

        preco_str = self.preco_entry.get().strip().replace(",", ".")
        try:
            preco = float(preco_str) if preco_str else 0
        except ValueError:
            self.preco_entry.configure(border_color=COLORS["danger_red"])
            return

        data = {
            "titulo": titulo,
            "preco": preco,
            "categoria": self.categoria_entry.get().strip(),
            "condicao": self.condicao_menu.get(),
            "localizacao": self.localizacao_entry.get().strip(),
            "descricao": self.descricao_text.get("1.0", "end-1c").strip(),
            "custom_fields": self._get_custom_fields(),
            "status": self._listing_data.get("status", "ativo"),
        }

        if self._on_save:
            self._on_save(data, self._image_paths)

        self.destroy()
