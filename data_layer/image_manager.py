"""
Image Manager - Gerenciamento de imagens locais dos anuncios.
Copia, lista, deleta imagens organizadas por listing_id.
"""

import shutil
import re
from pathlib import Path

from gui.utils.paths import get_images_dir


class ImageManager:
    # Extensoes de imagem suportadas
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}

    def __init__(self):
        self.IMAGES_DIR = get_images_dir()

    def get_listing_dir(self, listing_id: str) -> Path:
        """Retorna diretorio de imagens do anuncio, criando se necessario."""
        path = self.IMAGES_DIR / listing_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_images(self, listing_id: str) -> list:
        """Retorna lista de caminhos absolutos das imagens, ordenados."""
        listing_dir = self.IMAGES_DIR / listing_id
        if not listing_dir.exists():
            return []

        images = []
        for f in sorted(listing_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                images.append(str(f.absolute()))
        return images

    def add_images(self, listing_id: str, source_paths: list) -> list:
        """Copia imagens para pasta do anuncio. Retorna novos caminhos."""
        listing_dir = self.get_listing_dir(listing_id)

        # Determinar proximo indice
        existing = self.get_images(listing_id)
        next_idx = len(existing)

        new_paths = []
        for path_str in source_paths:
            source = Path(path_str)
            if not source.exists():
                continue

            ext = source.suffix.lower()
            if ext not in self.SUPPORTED_EXTENSIONS:
                continue

            # Nome com indice para manter ordem
            safe_name = self._sanitize_filename(source.stem)
            dest_name = f"{next_idx:03d}_{safe_name}{ext}"
            dest = listing_dir / dest_name

            shutil.copy2(str(source), str(dest))
            new_paths.append(str(dest.absolute()))
            next_idx += 1

        return new_paths

    def replace_images(self, listing_id: str, source_paths: list) -> list:
        """Remove imagens existentes e adiciona novas."""
        self.delete_listing_images(listing_id)
        return self.add_images(listing_id, source_paths)

    def delete_listing_images(self, listing_id: str):
        """Remove toda a pasta de imagens do anuncio."""
        listing_dir = self.IMAGES_DIR / listing_id
        if listing_dir.exists():
            shutil.rmtree(str(listing_dir))

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Remove caracteres problematicos do nome do arquivo."""
        sanitized = re.sub(r'[^\w\s\-.]', '', name)
        sanitized = re.sub(r'\s+', '_', sanitized)
        return sanitized[:50]  # limitar tamanho
