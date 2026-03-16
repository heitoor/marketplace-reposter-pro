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


def main():
    setup_logging()

    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
