"""
Database - Operacoes low-level SQLite.
Schema, conexao, CRUD basico com thread safety e migracoes.
"""

import logging
import sqlite3
import threading

from gui.utils.paths import get_db_path

logger = logging.getLogger(__name__)

# Schema version history - each migration is applied incrementally
MIGRATIONS = [
    # v1: Schema inicial
    {
        "version": 1,
        "sql": """
            CREATE TABLE IF NOT EXISTS listings (
                id              TEXT PRIMARY KEY,
                titulo          TEXT NOT NULL,
                preco           REAL NOT NULL,
                categoria       TEXT NOT NULL DEFAULT '',
                condicao        TEXT NOT NULL DEFAULT 'Novo',
                descricao       TEXT NOT NULL DEFAULT '',
                localizacao     TEXT NOT NULL DEFAULT '',
                status          TEXT NOT NULL DEFAULT 'ativo',
                link_anuncio    TEXT DEFAULT '',
                data_publicacao TEXT DEFAULT '',
                post_count      INTEGER NOT NULL DEFAULT 0,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS custom_fields (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id  TEXT NOT NULL,
                field_key   TEXT NOT NULL,
                field_value TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
                UNIQUE(listing_id, field_key)
            );

            CREATE INDEX IF NOT EXISTS idx_listings_status
                ON listings(status);
            CREATE INDEX IF NOT EXISTS idx_custom_fields_listing
                ON custom_fields(listing_id);
        """,
    },
    # v2: Adicionar coluna repost_state para tracking de estado intermediario
    {
        "version": 2,
        "sql": """
            ALTER TABLE listings ADD COLUMN repost_state TEXT DEFAULT NULL;
        """,
    },
]


class Database:

    def __init__(self):
        self.DB_PATH = get_db_path()
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(str(self.DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._run_migrations()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _get_schema_version(self) -> int:
        """Retorna versao atual do schema."""
        try:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
            )
            row = self.conn.execute("SELECT MAX(version) as v FROM schema_version").fetchone()
            return row["v"] if row and row["v"] is not None else 0
        except sqlite3.Error:
            return 0

    def _run_migrations(self):
        """Aplica migracoes pendentes."""
        current_version = self._get_schema_version()
        applied = 0

        for migration in MIGRATIONS:
            if migration["version"] > current_version:
                try:
                    self.conn.executescript(migration["sql"])
                    self.conn.execute(
                        "INSERT INTO schema_version (version) VALUES (?)",
                        (migration["version"],),
                    )
                    self.conn.commit()
                    applied += 1
                    logger.info("Migracao v%d aplicada com sucesso", migration["version"])
                except sqlite3.Error as e:
                    logger.error("Erro na migracao v%d: %s", migration["version"], e)
                    self.conn.rollback()
                    raise

        if applied:
            logger.info("Banco atualizado: %d migracoes aplicadas (v%d -> v%d)",
                        applied, current_version, current_version + applied)

    def execute(self, sql: str, params: tuple = ()):
        """Executa SQL com commit. Thread-safe com rollback em erro."""
        with self._lock:
            try:
                cursor = self.conn.execute(sql, params)
                self.conn.commit()
                return cursor
            except sqlite3.IntegrityError as e:
                self.conn.rollback()
                logger.error("Erro de integridade: %s | SQL: %s", e, sql)
                raise
            except sqlite3.OperationalError as e:
                self.conn.rollback()
                logger.error("Erro operacional: %s | SQL: %s", e, sql)
                raise
            except sqlite3.Error as e:
                self.conn.rollback()
                logger.error("Erro SQLite: %s | SQL: %s", e, sql)
                raise

    def executemany(self, sql: str, params_list: list):
        """Executa SQL para multiplos registros. Thread-safe."""
        with self._lock:
            try:
                cursor = self.conn.executemany(sql, params_list)
                self.conn.commit()
                return cursor
            except sqlite3.Error as e:
                self.conn.rollback()
                logger.error("Erro em executemany: %s | SQL: %s", e, sql)
                raise

    def execute_script(self, sql: str):
        """Executa bloco SQL. Thread-safe."""
        with self._lock:
            try:
                self.conn.executescript(sql)
            except sqlite3.Error as e:
                logger.error("Erro em execute_script: %s", e)
                raise

    def fetchone(self, sql: str, params: tuple = ()):
        """Busca um registro."""
        with self._lock:
            return self.conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: tuple = ()):
        """Busca todos os registros."""
        with self._lock:
            return self.conn.execute(sql, params).fetchall()

    def close(self):
        """Fecha conexao."""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None
