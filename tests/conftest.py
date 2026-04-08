"""
Fixtures compartilhados para todos os testes.
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Adiciona raiz do projeto ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture
def temp_dir():
    """Cria diretorio temporario que e limpo apos o teste."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def mock_app_dirs(temp_dir):
    """Mocka todos os caminhos da aplicacao para usar diretorio temporario."""
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    images_dir = data_dir / "images"
    images_dir.mkdir()

    env_path = data_dir / ".env"
    env_path.write_text(
        "MIN_DELAY=3\nMAX_DELAY=8\nDELAY_BETWEEN_POSTS=420\nHEADLESS=False\n",
        encoding="utf-8",
    )

    with patch("gui.utils.paths.get_data_dir", return_value=data_dir), \
         patch("gui.utils.paths.get_db_path", return_value=data_dir / "reposter.db"), \
         patch("gui.utils.paths.get_images_dir", return_value=images_dir), \
         patch("gui.utils.paths.get_env_path", return_value=env_path), \
         patch("gui.utils.paths.get_chrome_profile_dir", return_value=data_dir / "chrome_profile"), \
         patch("gui.utils.paths.get_cookies_path", return_value=data_dir / "fb_cookies.pkl"), \
         patch("data_layer.database.get_db_path", return_value=data_dir / "reposter.db"), \
         patch("data_layer.image_manager.get_images_dir", return_value=images_dir), \
         patch("gui.utils.settings_manager.get_env_path", return_value=env_path):
        yield {
            "data_dir": data_dir,
            "images_dir": images_dir,
            "db_path": data_dir / "reposter.db",
            "env_path": env_path,
        }


@pytest.fixture
def sample_listing_data():
    """Dados de exemplo para criar um listing."""
    return {
        "titulo": "iPhone 15 Pro Max 256GB",
        "preco": 5999.99,
        "categoria": "Eletronicos",
        "condicao": "Usado - Bom",
        "descricao": "iPhone em otimo estado, com caixa e acessorios originais.",
        "localizacao": "Sao Paulo, SP",
        "status": "ativo",
    }


@pytest.fixture
def sample_listing_data_2():
    """Segundo conjunto de dados de exemplo."""
    return {
        "titulo": "MacBook Air M2 2023",
        "preco": 8500.00,
        "categoria": "Eletronicos",
        "condicao": "Novo",
        "descricao": "MacBook novo, lacrado na caixa.",
        "localizacao": "Rio de Janeiro, RJ",
        "status": "ativo",
    }


@pytest.fixture
def sample_images(temp_dir):
    """Cria imagens fake para testes."""
    imgs = []
    for i in range(3):
        img_path = temp_dir / f"test_image_{i}.jpg"
        # Cria arquivo minimo JPEG (header valido)
        img_path.write_bytes(
            b'\xff\xd8\xff\xe0' + b'\x00' * 100 + b'\xff\xd9'
        )
        imgs.append(str(img_path))
    return imgs
