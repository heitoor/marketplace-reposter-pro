"""
Browser Setup - Configuracao compartilhada do Chrome WebDriver.
Usado pelo MarketplaceReposter e MarketplaceScraper.
"""

import os
import subprocess
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

from gui.utils.paths import get_chrome_profile_dir

logger = logging.getLogger(__name__)

SELENIUM_TIMEOUT = 20


def _kill_chrome_profile_processes(profile_dir: str):
    """Mata processos Chrome que estejam usando o perfil do app (Windows)."""
    try:
        result = subprocess.run(
            ["wmic", "process", "where",
             "name='chrome.exe'", "get", "CommandLine,ProcessId",
             "/FORMAT:LIST"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        # Normalizar separadores para comparacao
        profile_norm = profile_dir.replace("/", "\\").lower()

        current_pid = None
        current_cmd = None
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("CommandLine="):
                current_cmd = line
            elif line.startswith("ProcessId="):
                current_pid = line.split("=", 1)[1].strip()
                if current_cmd and profile_norm in current_cmd.lower():
                    logger.info("Matando Chrome orfao (PID %s) usando perfil do app", current_pid)
                    subprocess.run(
                        ["taskkill", "/F", "/PID", current_pid],
                        capture_output=True, timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                current_pid = None
                current_cmd = None
    except Exception as e:
        logger.debug("Nao foi possivel verificar processos Chrome: %s", e)


def create_chrome_driver(headless=None, timeout=SELENIUM_TIMEOUT):
    """
    Cria e configura Chrome WebDriver com perfil persistente e anti-deteccao.

    Args:
        headless: Se True, roda sem janela. None = lê do env.
        timeout: Timeout do WebDriverWait em segundos.

    Returns:
        Tupla (driver, wait).

    Raises:
        RuntimeError: Se nao conseguir iniciar o Chrome.
    """
    chrome_options = Options()

    # Anti-deteccao
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-extensions')

    # Fingerprint hardening
    chrome_options.add_argument('--disable-webgl')
    chrome_options.add_argument('--disable-canvas-antialiasing')
    chrome_options.add_argument('--disable-accelerated-2d-canvas')

    # Performance
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')

    # Perfil persistente - mantem login entre sessoes
    profile_dir = get_chrome_profile_dir()

    # Matar processos Chrome orfaos que travam o perfil
    _kill_chrome_profile_processes(str(profile_dir))

    # Remover lock file que impede o Chrome de iniciar
    lock_file = profile_dir / "SingletonLock"
    if lock_file.exists():
        try:
            lock_file.unlink()
            logger.info("Lock file removido: %s", lock_file)
        except OSError:
            pass

    chrome_options.add_argument(f'--user-data-dir={profile_dir}')

    # Headless
    if headless is None:
        headless = os.getenv('HEADLESS', 'False').lower() == 'true'
    if headless:
        chrome_options.add_argument('--headless=new')

    try:
        # Selenium >= 4.6 usa o selenium-manager builtin para baixar
        # o ChromeDriver automaticamente se nao estiver no PATH
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, timeout)

        # Ocultar webdriver property
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        # Ocultar plugins e languages padrao de automacao
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en-US', 'en'],
                });
                window.chrome = { runtime: {} };
            """
        })

        logger.info("WebDriver configurado com sucesso")
        return driver, wait

    except Exception as e:
        logger.error("Falha ao configurar Chrome: %s", e, exc_info=True)
        raise RuntimeError(
            f"Erro ao configurar Chrome: {e}. "
            "Certifique-se de ter o Google Chrome instalado."
        ) from e
