"""
Constantes de tema e cores para a GUI.
Dark Mode com acentos em azul.
"""

import sys

# Fonte principal - Segoe UI no Windows, fallback para sans-serif em outros OS
if sys.platform == "win32":
    _FONT_FAMILY = "Segoe UI"
    _MONO_FAMILY = "Consolas"
elif sys.platform == "darwin":
    _FONT_FAMILY = "SF Pro Display"
    _MONO_FAMILY = "SF Mono"
else:
    _FONT_FAMILY = "Ubuntu"
    _MONO_FAMILY = "Ubuntu Mono"

COLORS = {
    # Backgrounds
    "bg_dark": "#1a1a2e",
    "bg_frame": "#16213e",
    "log_bg": "#0f0f23",

    # Accent
    "accent_blue": "#4A9EFF",
    "accent_blue_hover": "#3A8EEF",

    # Status
    "success_green": "#2ECC71",
    "success_green_hover": "#27AE60",
    "danger_red": "#E74C3C",
    "danger_red_hover": "#C0392B",
    "warning_yellow": "#F39C12",

    # Text
    "text_primary": "#FFFFFF",
    "text_secondary": "#888888",
    "text_log": "#e0e0e0",

    # Status indicators
    "status_connected": "#2ECC71",
    "status_pending": "#F39C12",
    "status_disconnected": "#E74C3C",

    # Table
    "table_header_bg": "#1e2a4a",
    "table_row_bg": "#16213e",
    "table_row_alt_bg": "#1a2540",
    "table_row_hover": "#1e3055",
    "table_row_selected": "#2a4070",

    # Listing status
    "status_ativo": "#2ECC71",
    "status_pausado": "#F39C12",
    "status_vendido": "#95A5A6",
}

FONTS = {
    "title": (_FONT_FAMILY, 24, "bold"),
    "subtitle": (_FONT_FAMILY, 13),
    "button": (_FONT_FAMILY, 14, "bold"),
    "button_small": (_FONT_FAMILY, 12),
    "label": (_FONT_FAMILY, 13),
    "log": (_MONO_FAMILY, 12),
    "status": (_FONT_FAMILY, 11),
    "table_header": (_FONT_FAMILY, 12, "bold"),
    "table_cell": (_FONT_FAMILY, 12),
    "dialog_title": (_FONT_FAMILY, 18, "bold"),
    "section_title": (_FONT_FAMILY, 14, "bold"),
}

APP_NAME = "EITO LABS"
from gui.utils.paths import APP_VERSION

APP_SUBTITLE = f"Marketplace Reposter Pro v{APP_VERSION}"
WINDOW_SIZE = "1100x700"
WINDOW_MIN_SIZE = (1000, 600)
