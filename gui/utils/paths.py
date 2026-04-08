"""
Paths centralizados - todos os dados do usuario ficam em AppData.
Funciona tanto em dev (python gui_app.py) quanto no .exe (PyInstaller).
"""

import os
import sys
from pathlib import Path

APP_NAME = "MarketplaceReposterPro"
APP_VERSION = "3.1.1"


def get_app_dir() -> Path:
    """Retorna diretorio base da aplicacao (onde esta o .exe ou o script)."""
    if getattr(sys, 'frozen', False):
        # Rodando como .exe (PyInstaller)
        return Path(sys.executable).parent
    # Rodando como script
    return Path(__file__).parent.parent.parent


def get_data_dir() -> Path:
    """Retorna diretorio de dados do usuario em AppData/Local."""
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    data_dir = base / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    """Caminho do banco SQLite."""
    return get_data_dir() / "reposter.db"


def get_images_dir() -> Path:
    """Diretorio de imagens dos anuncios."""
    images_dir = get_data_dir() / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir


def get_cookies_path() -> Path:
    """Caminho do arquivo de cookies do Facebook."""
    return get_data_dir() / "fb_cookies.pkl"


def get_chrome_profile_dir() -> Path:
    """Diretorio do perfil Chrome persistente (guarda login, senhas, sessao)."""
    profile_dir = get_data_dir() / "chrome_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    return profile_dir


def get_env_path() -> Path:
    """Caminho do .env (configuracoes).
    Fica no AppData para sobreviver a atualizacoes do instalador."""
    env_path = get_data_dir() / ".env"
    if not env_path.exists():
        # Copia o .env padrao da pasta do app, se existir
        app_env = get_app_dir() / ".env"
        if app_env.exists():
            import shutil
            shutil.copy2(str(app_env), str(env_path))
        else:
            # Cria .env com defaults
            env_path.write_text(
                "MIN_DELAY=3\nMAX_DELAY=8\nDELAY_BETWEEN_POSTS=420\nHEADLESS=False\n",
                encoding="utf-8",
            )
    return env_path
