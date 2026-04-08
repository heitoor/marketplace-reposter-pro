"""
Testes para data_layer/image_manager.py
Cobre: add, get, replace, delete, sanitizacao de nomes.
"""

from pathlib import Path
import pytest


class TestImageManager:

    def _get_manager(self):
        from data_layer.image_manager import ImageManager
        return ImageManager()

    def test_get_images_empty(self, mock_app_dirs):
        im = self._get_manager()
        images = im.get_images("nonexistent-listing")
        assert images == []

    def test_add_images(self, mock_app_dirs, sample_images):
        im = self._get_manager()
        new_paths = im.add_images("listing-1", sample_images)
        assert len(new_paths) == 3
        for p in new_paths:
            assert Path(p).exists()

    def test_add_images_preserves_order(self, mock_app_dirs, sample_images):
        im = self._get_manager()
        im.add_images("listing-1", sample_images)
        images = im.get_images("listing-1")
        assert len(images) == 3
        # Nomes devem comecar com 000_, 001_, 002_
        names = [Path(p).name for p in images]
        assert names[0].startswith("000_")
        assert names[1].startswith("001_")
        assert names[2].startswith("002_")

    def test_add_images_increments_index(self, mock_app_dirs, sample_images):
        """Adicionar mais imagens deve continuar o indice."""
        im = self._get_manager()
        im.add_images("listing-1", sample_images[:2])
        im.add_images("listing-1", sample_images[2:])
        images = im.get_images("listing-1")
        assert len(images) == 3
        names = [Path(p).name for p in images]
        assert names[2].startswith("002_")

    def test_get_images_returns_absolute_paths(self, mock_app_dirs, sample_images):
        im = self._get_manager()
        im.add_images("listing-1", sample_images)
        images = im.get_images("listing-1")
        for p in images:
            assert Path(p).is_absolute()

    def test_replace_images(self, mock_app_dirs, sample_images, temp_dir):
        im = self._get_manager()
        im.add_images("listing-1", sample_images)
        assert len(im.get_images("listing-1")) == 3

        # Criar nova imagem
        new_img = temp_dir / "new_image.jpg"
        new_img.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 50 + b'\xff\xd9')

        im.replace_images("listing-1", [str(new_img)])
        images = im.get_images("listing-1")
        assert len(images) == 1

    def test_delete_listing_images(self, mock_app_dirs, sample_images):
        im = self._get_manager()
        im.add_images("listing-1", sample_images)
        listing_dir = im.IMAGES_DIR / "listing-1"
        assert listing_dir.exists()

        im.delete_listing_images("listing-1")
        assert not listing_dir.exists()

    def test_delete_nonexistent_listing(self, mock_app_dirs):
        """Deletar imagens de listing inexistente nao deve falhar."""
        im = self._get_manager()
        im.delete_listing_images("nonexistent")  # Nao deve levantar excecao

    def test_unsupported_extension_ignored(self, mock_app_dirs, temp_dir):
        im = self._get_manager()
        txt_file = temp_dir / "doc.txt"
        txt_file.write_text("not an image")
        new_paths = im.add_images("listing-1", [str(txt_file)])
        assert len(new_paths) == 0

    def test_nonexistent_source_ignored(self, mock_app_dirs):
        im = self._get_manager()
        new_paths = im.add_images("listing-1", ["/fake/path/img.jpg"])
        assert len(new_paths) == 0

    def test_supported_extensions(self, mock_app_dirs, temp_dir):
        im = self._get_manager()
        extensions = [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"]
        paths = []
        for ext in extensions:
            f = temp_dir / f"img{ext}"
            f.write_bytes(b'\x00' * 50)
            paths.append(str(f))
        new_paths = im.add_images("listing-ext", paths)
        assert len(new_paths) == len(extensions)

    def test_get_listing_dir_creates_directory(self, mock_app_dirs):
        im = self._get_manager()
        d = im.get_listing_dir("new-listing-123")
        assert d.exists()
        assert d.is_dir()


class TestSanitizeFilename:

    def test_basic_sanitization(self):
        from data_layer.image_manager import ImageManager
        assert ImageManager._sanitize_filename("hello world") == "hello_world"

    def test_special_chars_removed(self):
        from data_layer.image_manager import ImageManager
        result = ImageManager._sanitize_filename("foto@#$%&*()")
        assert "@" not in result
        assert "#" not in result

    def test_max_length(self):
        from data_layer.image_manager import ImageManager
        long_name = "a" * 100
        result = ImageManager._sanitize_filename(long_name)
        assert len(result) <= 50

    def test_empty_string(self):
        from data_layer.image_manager import ImageManager
        result = ImageManager._sanitize_filename("")
        assert result == ""

    def test_unicode_preserved(self):
        from data_layer.image_manager import ImageManager
        result = ImageManager._sanitize_filename("foto_café")
        assert "caf" in result
