"""
Gerenciador de configuracoes - leitura e escrita do arquivo .env
"""

import os
from dotenv import load_dotenv

from gui.utils.paths import get_env_path


class SettingsManager:
    """Carrega e salva configuracoes do arquivo .env"""

    DEFAULTS = {
        "min_delay": 3,
        "max_delay": 8,
        "delay_between_posts": 420,
        "repost_interval_days": 7,
        "headless": False,
    }

    KEY_MAP = {
        "min_delay": "MIN_DELAY",
        "max_delay": "MAX_DELAY",
        "delay_between_posts": "DELAY_BETWEEN_POSTS",
        "repost_interval_days": "REPOST_INTERVAL_DAYS",
        "headless": "HEADLESS",
    }

    @classmethod
    def load(cls) -> dict:
        """Carrega configuracoes do .env, com fallback para defaults."""
        env_path = get_env_path()
        load_dotenv(env_path, override=True)
        settings = {}
        for key, env_name in cls.KEY_MAP.items():
            value = os.getenv(env_name)
            if value is None:
                settings[key] = cls.DEFAULTS[key]
            elif key == "headless":
                settings[key] = value.lower() == "true"
            else:
                try:
                    settings[key] = int(value)
                except ValueError:
                    settings[key] = cls.DEFAULTS[key]
        return settings

    @classmethod
    def save(cls, settings: dict):
        """Salva configuracoes no .env, preservando comentarios."""
        env_path = get_env_path()
        lines = []
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        updates = {}
        for key, env_name in cls.KEY_MAP.items():
            if key in settings:
                val = settings[key]
                if isinstance(val, bool):
                    val = str(val)
                updates[env_name] = str(val)

        found_keys = set()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                eq_pos = stripped.find("=")
                if eq_pos > 0:
                    var_name = stripped[:eq_pos].strip()
                    if var_name in updates:
                        new_lines.append(f"{var_name}={updates[var_name]}\n")
                        found_keys.add(var_name)
                        continue
            new_lines.append(line)

        for env_name, value in updates.items():
            if env_name not in found_keys:
                new_lines.append(f"{env_name}={value}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
