"""
Updater - Verifica e aplica atualizacoes automaticamente.
1. Consulta version.json remoto (GitHub Gist)
2. Se versao nova disponivel, baixa o instalador
3. Executa o instalador silenciosamente e fecha o app
"""

import os
import sys
import threading
import logging
import tempfile
import subprocess
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError
import json

from gui.utils.paths import APP_VERSION, get_data_dir

logger = logging.getLogger(__name__)

VERSION_CHECK_URL = "https://gist.githubusercontent.com/heitoor/4d60d5d8fb0d3322974ff46b812112a5/raw/version.json"

# Tamanho do buffer de download (8KB)
DOWNLOAD_CHUNK_SIZE = 8192


def parse_version(version_str: str) -> tuple:
    """Converte '3.1.0' em (3, 1, 0) para comparacao."""
    try:
        return tuple(int(x) for x in version_str.strip().split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def check_for_updates(callback):
    """
    Verifica atualizacao em background.
    Chama callback(update_info) se houver versao nova.
    update_info = {"version": "x.y.z", "download_url": "...", "notes": "..."}
    Chama callback(None) se estiver atualizado ou em caso de erro.

    NOTA: callback e chamado de uma thread de background.
    Para uso com Tkinter, envolva com root.after(0, ...).
    """

    def _check():
        try:
            req = Request(VERSION_CHECK_URL, headers={"User-Agent": "MarketplaceReposterPro"})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            remote_version = data.get("version", "0.0.0")

            if parse_version(remote_version) > parse_version(APP_VERSION):
                logger.info("Atualizacao disponivel: v%s -> v%s", APP_VERSION, remote_version)
                callback(data)
            else:
                logger.info("App atualizado (v%s)", APP_VERSION)
                callback(None)

        except (URLError, json.JSONDecodeError, OSError) as e:
            logger.debug("Nao foi possivel verificar atualizacoes: %s", e)
            callback(None)

    thread = threading.Thread(target=_check, daemon=True)
    thread.start()


def download_update(download_url: str, progress_callback=None) -> str:
    """
    Baixa o instalador da atualizacao.

    Args:
        download_url: URL direta do .exe do instalador.
        progress_callback: Funcao(downloaded_bytes, total_bytes) chamada durante download.

    Returns:
        Caminho local do arquivo baixado.

    Raises:
        Exception: Se o download falhar.
    """
    # Diretorio de updates no AppData
    update_dir = get_data_dir() / "updates"
    update_dir.mkdir(parents=True, exist_ok=True)

    # Limpar downloads antigos
    for old_file in update_dir.glob("*.exe"):
        try:
            old_file.unlink()
        except OSError:
            pass

    filename = download_url.split("/")[-1]
    if not filename.endswith(".exe"):
        filename = "MarketplaceReposterPro_Setup.exe"

    dest_path = update_dir / filename

    logger.info("Baixando atualizacao de: %s", download_url)

    req = Request(download_url, headers={"User-Agent": "MarketplaceReposterPro"})
    response = urlopen(req, timeout=120)

    total_size = response.headers.get("Content-Length")
    total_size = int(total_size) if total_size else 0

    downloaded = 0
    with open(str(dest_path), "wb") as f:
        while True:
            chunk = response.read(DOWNLOAD_CHUNK_SIZE)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if progress_callback:
                progress_callback(downloaded, total_size)

    logger.info("Download concluido: %s (%d bytes)", dest_path, downloaded)
    return str(dest_path)


def apply_update(installer_path: str):
    """
    Executa o instalador silenciosamente e encerra o app.
    O Inno Setup com /SILENT atualiza sem perguntas, mantendo dados do usuario.
    """
    logger.info("Aplicando atualizacao: %s", installer_path)

    # /SILENT = instala sem dialogs (mostra barra de progresso minima)
    # /CLOSEAPPLICATIONS = fecha o app se estiver rodando
    # /RESTARTAPPLICATIONS = reabre o app apos instalar
    # /NORESTART = nao reinicia o Windows
    subprocess.Popen(
        [installer_path, "/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS", "/NORESTART"],
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

    # Dar tempo pro installer iniciar antes de sair
    logger.info("Installer iniciado. Encerrando app para atualizar...")

    # Forcar saida do app - o installer vai substituir os arquivos
    os._exit(0)
