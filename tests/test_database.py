"""
Testes para data_layer/database.py
Cobre: inicializacao, migracoes, CRUD thread-safe, rollback em erro.
"""

import sqlite3
import threading
import pytest


class TestDatabaseInitialization:
    """Testa inicializacao do banco e migracoes."""

    def test_creates_database_file(self, mock_app_dirs):
        from data_layer.database import Database
        db = Database()
        assert mock_app_dirs["db_path"].exists()
        db.close()

    def test_creates_listings_table(self, mock_app_dirs):
        from data_layer.database import Database
        db = Database()
        row = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='listings'"
        )
        assert row is not None
        assert row["name"] == "listings"
        db.close()

    def test_creates_custom_fields_table(self, mock_app_dirs):
        from data_layer.database import Database
        db = Database()
        row = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='custom_fields'"
        )
        assert row is not None
        db.close()

    def test_creates_schema_version_table(self, mock_app_dirs):
        from data_layer.database import Database
        db = Database()
        row = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        assert row is not None
        db.close()

    def test_schema_version_is_latest(self, mock_app_dirs):
        from data_layer.database import Database, MIGRATIONS
        db = Database()
        row = db.fetchone("SELECT MAX(version) as v FROM schema_version")
        assert row["v"] == MIGRATIONS[-1]["version"]
        db.close()

    def test_wal_mode_enabled(self, mock_app_dirs):
        from data_layer.database import Database
        db = Database()
        row = db.fetchone("PRAGMA journal_mode")
        assert row[0] == "wal"
        db.close()

    def test_foreign_keys_enabled(self, mock_app_dirs):
        from data_layer.database import Database
        db = Database()
        row = db.fetchone("PRAGMA foreign_keys")
        assert row[0] == 1
        db.close()

    def test_repost_state_column_exists(self, mock_app_dirs):
        """Migration v2 deve adicionar coluna repost_state."""
        from data_layer.database import Database
        db = Database()
        # Inserir um registro para verificar que a coluna existe
        db.execute(
            "INSERT INTO listings (id, titulo, preco, created_at, updated_at, repost_state) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("test-id", "Test", 100, "2024-01-01", "2024-01-01", "pending")
        )
        row = db.fetchone("SELECT repost_state FROM listings WHERE id = ?", ("test-id",))
        assert row["repost_state"] == "pending"
        db.close()

    def test_idempotent_migrations(self, mock_app_dirs):
        """Criar Database duas vezes nao deve falhar (migracoes ja aplicadas)."""
        from data_layer.database import Database
        db1 = Database()
        db1.close()
        db2 = Database()
        row = db2.fetchone("SELECT COUNT(*) as cnt FROM schema_version")
        assert row["cnt"] == 2  # v1 + v2
        db2.close()


class TestDatabaseCRUD:
    """Testa operacoes CRUD."""

    def test_execute_insert_and_fetchone(self, mock_app_dirs):
        from data_layer.database import Database
        db = Database()
        db.execute(
            "INSERT INTO listings (id, titulo, preco, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("id-1", "Produto A", 100.0, "2024-01-01", "2024-01-01")
        )
        row = db.fetchone("SELECT * FROM listings WHERE id = ?", ("id-1",))
        assert row["titulo"] == "Produto A"
        assert row["preco"] == 100.0
        db.close()

    def test_execute_update(self, mock_app_dirs):
        from data_layer.database import Database
        db = Database()
        db.execute(
            "INSERT INTO listings (id, titulo, preco, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("id-1", "Produto A", 100.0, "2024-01-01", "2024-01-01")
        )
        db.execute("UPDATE listings SET preco = ? WHERE id = ?", (200.0, "id-1"))
        row = db.fetchone("SELECT preco FROM listings WHERE id = ?", ("id-1",))
        assert row["preco"] == 200.0
        db.close()

    def test_execute_delete(self, mock_app_dirs):
        from data_layer.database import Database
        db = Database()
        db.execute(
            "INSERT INTO listings (id, titulo, preco, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("id-1", "Produto A", 100.0, "2024-01-01", "2024-01-01")
        )
        db.execute("DELETE FROM listings WHERE id = ?", ("id-1",))
        row = db.fetchone("SELECT * FROM listings WHERE id = ?", ("id-1",))
        assert row is None
        db.close()

    def test_fetchall(self, mock_app_dirs):
        from data_layer.database import Database
        db = Database()
        for i in range(5):
            db.execute(
                "INSERT INTO listings (id, titulo, preco, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (f"id-{i}", f"Produto {i}", i * 10.0, "2024-01-01", "2024-01-01")
            )
        rows = db.fetchall("SELECT * FROM listings")
        assert len(rows) == 5
        db.close()

    def test_executemany(self, mock_app_dirs):
        from data_layer.database import Database
        db = Database()
        params = [
            (f"id-{i}", f"Produto {i}", i * 10.0, "2024-01-01", "2024-01-01")
            for i in range(10)
        ]
        db.executemany(
            "INSERT INTO listings (id, titulo, preco, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            params
        )
        rows = db.fetchall("SELECT * FROM listings")
        assert len(rows) == 10
        db.close()

    def test_integrity_error_rollback(self, mock_app_dirs):
        """Inserir ID duplicado deve fazer rollback."""
        from data_layer.database import Database
        db = Database()
        db.execute(
            "INSERT INTO listings (id, titulo, preco, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("id-dup", "Produto", 100.0, "2024-01-01", "2024-01-01")
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO listings (id, titulo, preco, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                ("id-dup", "Duplicado", 200.0, "2024-01-01", "2024-01-01")
            )
        # Registro original intacto
        row = db.fetchone("SELECT titulo FROM listings WHERE id = ?", ("id-dup",))
        assert row["titulo"] == "Produto"
        db.close()

    def test_foreign_key_cascade_delete(self, mock_app_dirs):
        """Deletar listing deve deletar custom_fields associados."""
        from data_layer.database import Database
        db = Database()
        db.execute(
            "INSERT INTO listings (id, titulo, preco, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("id-fk", "Produto FK", 100.0, "2024-01-01", "2024-01-01")
        )
        db.execute(
            "INSERT INTO custom_fields (listing_id, field_key, field_value) VALUES (?, ?, ?)",
            ("id-fk", "cor", "azul")
        )
        db.execute("DELETE FROM listings WHERE id = ?", ("id-fk",))
        row = db.fetchone("SELECT * FROM custom_fields WHERE listing_id = ?", ("id-fk",))
        assert row is None
        db.close()


class TestDatabaseThreadSafety:
    """Testa operacoes concorrentes."""

    def test_concurrent_inserts(self, mock_app_dirs):
        from data_layer.database import Database
        db = Database()
        errors = []

        def insert_batch(start, count):
            try:
                for i in range(start, start + count):
                    db.execute(
                        "INSERT INTO listings (id, titulo, preco, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (f"thread-{i}", f"Prod {i}", i, "2024-01-01", "2024-01-01")
                    )
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=insert_batch, args=(i * 20, 20))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Erros em threads: {errors}"
        rows = db.fetchall("SELECT * FROM listings")
        assert len(rows) == 100
        db.close()

    def test_concurrent_reads_and_writes(self, mock_app_dirs):
        from data_layer.database import Database
        db = Database()
        # Inserir dados base
        for i in range(50):
            db.execute(
                "INSERT INTO listings (id, titulo, preco, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (f"rw-{i}", f"Prod {i}", i, "2024-01-01", "2024-01-01")
            )

        read_results = []
        errors = []

        def reader():
            try:
                for _ in range(20):
                    rows = db.fetchall("SELECT * FROM listings")
                    read_results.append(len(rows))
            except Exception as e:
                errors.append(e)

        def writer():
            try:
                for i in range(50, 70):
                    db.execute(
                        "INSERT INTO listings (id, titulo, preco, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (f"rw-{i}", f"Prod {i}", i, "2024-01-01", "2024-01-01")
                    )
            except Exception as e:
                errors.append(e)

        t_reader = threading.Thread(target=reader)
        t_writer = threading.Thread(target=writer)
        t_reader.start()
        t_writer.start()
        t_reader.join()
        t_writer.join()

        assert not errors
        # Todas as leituras devem retornar >= 50 registros
        assert all(r >= 50 for r in read_results)
        db.close()
