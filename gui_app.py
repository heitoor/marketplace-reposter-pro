#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EITO LABS - Marketplace Reposter Pro
Entry point da interface grafica.
"""

import logging
import sys
import io

# Forca UTF-8 no stdout/stderr (Windows com emojis)
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import customtkinter
from gui.utils.paths import get_data_dir
from gui.main_window import MainWindow


def setup_logging():
    """Configura logging para arquivo e console."""
    log_dir = get_data_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'reposter.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(str(log_file), encoding='utf-8'),
            logging.StreamHandler(),
        ]
    )
    logging.getLogger(__name__).info("Marketplace Reposter Pro iniciado")


def run_startup_backup():
    """Cria backup do banco na inicializacao (maximo 1 por dia)."""
    from gui.utils.paths import get_data_dir, get_db_path
    from datetime import datetime

    db_path = get_db_path()
    if not db_path.exists():
        return

    backup_dir = get_data_dir() / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime('%Y%m%d')
    today_backup = backup_dir / f"reposter_{today}.db"
    if today_backup.exists():
        return  # Ja tem backup de hoje

    import shutil
    try:
        shutil.copy2(str(db_path), str(today_backup))
        logging.getLogger(__name__).info("Backup diario criado: %s", today_backup.name)

        # Manter apenas os ultimos 7 backups
        backups = sorted(backup_dir.glob("reposter_*.db"), reverse=True)
        for old in backups[7:]:
            old.unlink(missing_ok=True)
    except Exception as e:
        logging.getLogger(__name__).warning("Falha no backup: %s", e)


def main():
    setup_logging()
    run_startup_backup()

    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
