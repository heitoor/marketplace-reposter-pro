"""
Updater - Verifica se ha versao mais recente disponivel.
Consulta um arquivo de versao remoto (GitHub raw ou endpoint proprio).
"""

import threading
import logging
from urllib.request import urlopen, Request
from urllib.error import URLError
import json

from gui.utils.paths import APP_VERSION

logger = logging.getLogger(__name__)

VERSION_CHECK_URL = "https://gist.githubusercontent.com/heitoor/4d60d5d8fb0d3322974ff46b812112a5/raw/version.json"


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
