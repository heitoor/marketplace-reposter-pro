"""
Testes para data_layer/local_data_manager.py
Cobre: CRUD completo, busca, repostagem, campos customizados.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest


class TestLocalDataManagerCRUD:
    """Testa operacoes CRUD via LocalDataManager."""

    def _get_manager(self):
        from data_layer.local_data_manager import LocalDataManager
        return LocalDataManager()

    def test_create_listing(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        assert lid is not None
        assert len(lid) == 36  # UUID format

    def test_get_listing(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        listing = dm.get_listing(lid)
        assert listing is not None
        assert listing["titulo"] == "iPhone 15 Pro Max 256GB"
        assert listing["preco"] == 5999.99
        assert listing["status"] == "ativo"

    def test_get_listing_not_found(self, mock_app_dirs):
        dm = self._get_manager()
        assert dm.get_listing("nonexistent-id") is None

    def test_get_all_listings(self, mock_app_dirs, sample_listing_data, sample_listing_data_2):
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])
        dm.create_listing(sample_listing_data_2, [])
        listings = dm.get_all_listings()
        assert len(listings) == 2

    def test_get_all_listings_empty(self, mock_app_dirs):
        dm = self._get_manager()
        listings = dm.get_all_listings()
        assert listings == []

    def test_update_listing(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        updated_data = sample_listing_data.copy()
        updated_data["titulo"] = "iPhone 15 ATUALIZADO"
        updated_data["preco"] = 4999.99
        result = dm.update_listing(lid, updated_data)
        assert result is True

        listing = dm.get_listing(lid)
        assert listing["titulo"] == "iPhone 15 ATUALIZADO"
        assert listing["preco"] == 4999.99

    def test_delete_listing(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        result = dm.delete_listing(lid)
        assert result is True
        assert dm.get_listing(lid) is None

    def test_delete_listings_batch(self, mock_app_dirs, sample_listing_data, sample_listing_data_2):
        dm = self._get_manager()
        lid1 = dm.create_listing(sample_listing_data, [])
        lid2 = dm.create_listing(sample_listing_data_2, [])
        count = dm.delete_listings([lid1, lid2])
        assert count == 2
        assert dm.get_all_listings() == []

    def test_update_status(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        dm.update_status(lid, "vendido")
        listing = dm.get_listing(lid)
        assert listing["status"] == "vendido"

    def test_update_statuses_batch(self, mock_app_dirs, sample_listing_data, sample_listing_data_2):
        dm = self._get_manager()
        lid1 = dm.create_listing(sample_listing_data, [])
        lid2 = dm.create_listing(sample_listing_data_2, [])
        count = dm.update_statuses([lid1, lid2], "pausado")
        assert count == 2
        for lid in [lid1, lid2]:
            assert dm.get_listing(lid)["status"] == "pausado"

    def test_create_listing_with_defaults(self, mock_app_dirs):
        dm = self._get_manager()
        lid = dm.create_listing({"titulo": "Minimo", "preco": 10}, [])
        listing = dm.get_listing(lid)
        assert listing["condicao"] == "Novo"
        assert listing["status"] == "ativo"
        assert listing["descricao"] == ""

    def test_create_listing_preco_string(self, mock_app_dirs):
        """Preco como string deve ser convertido para float."""
        dm = self._get_manager()
        lid = dm.create_listing({"titulo": "Test", "preco": "99.50"}, [])
        listing = dm.get_listing(lid)
        assert listing["preco"] == 99.50


class TestLocalDataManagerRepostagem:
    """Testa logica de repostagem."""

    def _get_manager(self):
        from data_layer.local_data_manager import LocalDataManager
        return LocalDataManager()

    def test_get_produtos_para_repostar_empty(self, mock_app_dirs):
        dm = self._get_manager()
        produtos = dm.get_produtos_para_repostar()
        assert produtos == []

    def test_listing_sem_data_deve_repostar(self, mock_app_dirs, sample_listing_data):
        """Listing ativo sem data_publicacao deve ser elegivel para repostagem."""
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])
        produtos = dm.get_produtos_para_repostar()
        assert len(produtos) == 1
        assert produtos[0]["Título"] == "iPhone 15 Pro Max 256GB"

    def test_listing_recente_nao_reposta(self, mock_app_dirs, sample_listing_data):
        """Listing postado hoje NAO deve ser repostado."""
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        hoje = datetime.now().strftime('%Y-%m-%d')
        dm.atualizar_apos_postagem(lid, hoje, "https://facebook.com/item/123", True)
        produtos = dm.get_produtos_para_repostar()
        assert len(produtos) == 0

    def test_listing_antigo_deve_repostar(self, mock_app_dirs, sample_listing_data):
        """Listing postado ha mais de 7 dias DEVE ser repostado."""
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        oito_dias_atras = (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d')
        dm.atualizar_apos_postagem(lid, oito_dias_atras, "https://facebook.com/item/123", True)
        produtos = dm.get_produtos_para_repostar()
        assert len(produtos) == 1

    def test_listing_pausado_nao_reposta(self, mock_app_dirs, sample_listing_data):
        """Listing com status pausado NAO deve ser repostado."""
        dm = self._get_manager()
        data = sample_listing_data.copy()
        data["status"] = "pausado"
        dm.create_listing(data, [])
        produtos = dm.get_produtos_para_repostar()
        assert len(produtos) == 0

    def test_listing_vendido_nao_reposta(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        data = sample_listing_data.copy()
        data["status"] = "vendido"
        dm.create_listing(data, [])
        produtos = dm.get_produtos_para_repostar()
        assert len(produtos) == 0

    def test_atualizar_apos_postagem_sucesso(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        result = dm.atualizar_apos_postagem(lid, "2024-06-01", "https://fb.com/item/999", True)
        assert result is True
        listing = dm.get_listing(lid)
        assert listing["link_anuncio"] == "https://fb.com/item/999"
        assert listing["data_publicacao"] == "2024-06-01"
        assert listing["post_count"] == 1

    def test_atualizar_apos_postagem_incrementa_contador(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        for i in range(3):
            dm.atualizar_apos_postagem(lid, f"2024-0{i+1}-01", f"https://fb.com/item/{i}", True)
        listing = dm.get_listing(lid)
        assert listing["post_count"] == 3

    def test_atualizar_apos_postagem_falha(self, mock_app_dirs, sample_listing_data):
        """Em caso de falha, post_count NAO deve incrementar."""
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        dm.atualizar_apos_postagem(lid, "", "", False)
        listing = dm.get_listing(lid)
        assert listing["post_count"] == 0

    def test_mapeamento_chaves_acentuadas(self, mock_app_dirs, sample_listing_data):
        """Verifica que o mapeamento de colunas retorna chaves acentuadas."""
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])
        produtos = dm.get_produtos_para_repostar()
        produto = produtos[0]
        assert "Título" in produto
        assert "Preço" in produto
        assert "Categoria" in produto
        assert "Condição" in produto
        assert "Descrição" in produto
        assert "Localização" in produto
        assert "Link Anúncio Atual" in produto
        assert "Data Publicação" in produto
        assert "id" in produto

    def test_update_link_and_date(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        dm.update_link_and_date(lid, "https://fb.com/item/456", "2024-03-15")
        listing = dm.get_listing(lid)
        assert listing["link_anuncio"] == "https://fb.com/item/456"
        assert listing["data_publicacao"] == "2024-03-15"

    def test_data_publicacao_truncada_para_10_chars(self, mock_app_dirs, sample_listing_data):
        """Data com hora deve ser truncada para YYYY-MM-DD."""
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        dm.atualizar_apos_postagem(lid, "2024-06-01 14:30:00", "https://fb.com/item/1", True)
        listing = dm.get_listing(lid)
        assert listing["data_publicacao"] == "2024-06-01"


class TestLocalDataManagerSearch:
    """Testa busca de listings."""

    def _get_manager(self):
        from data_layer.local_data_manager import LocalDataManager
        return LocalDataManager()

    def test_search_by_titulo(self, mock_app_dirs, sample_listing_data, sample_listing_data_2):
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])
        dm.create_listing(sample_listing_data_2, [])
        results = dm.search_listings("iPhone")
        assert len(results) == 1
        assert results[0]["titulo"] == "iPhone 15 Pro Max 256GB"

    def test_search_by_categoria(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])
        results = dm.search_listings("Eletronicos")
        assert len(results) == 1

    def test_search_by_localizacao(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])
        results = dm.search_listings("Sao Paulo")
        assert len(results) == 1

    def test_search_no_results(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])
        results = dm.search_listings("xyzabcdef123")
        assert len(results) == 0

    def test_search_case_insensitive(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])
        results = dm.search_listings("iphone")
        assert len(results) == 1

    def test_search_special_chars_escaped(self, mock_app_dirs, sample_listing_data):
        """Caracteres especiais do LIKE (%, _) devem ser escapados."""
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])
        # Estes nao devem causar SQL injection ou wildcards
        results = dm.search_listings("100%")
        assert len(results) == 0
        results = dm.search_listings("_phone")
        assert len(results) == 0


class TestLocalDataManagerCustomFields:
    """Testa campos customizados."""

    def _get_manager(self):
        from data_layer.local_data_manager import LocalDataManager
        return LocalDataManager()

    def test_set_and_get_custom_fields(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        dm.set_custom_fields(lid, {"cor": "preto", "tamanho": "256GB"})
        fields = dm.get_custom_fields(lid)
        assert fields["cor"] == "preto"
        assert fields["tamanho"] == "256GB"

    def test_replace_custom_fields(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        dm.set_custom_fields(lid, {"cor": "preto"})
        dm.set_custom_fields(lid, {"memoria": "256GB"})
        fields = dm.get_custom_fields(lid)
        assert "cor" not in fields  # foi substituido
        assert fields["memoria"] == "256GB"

    def test_empty_custom_fields(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        fields = dm.get_custom_fields(lid)
        assert fields == {}

    def test_custom_fields_via_create_listing(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        data = sample_listing_data.copy()
        data["custom_fields"] = {"cor": "branco", "garantia": "1 ano"}
        lid = dm.create_listing(data, [])
        fields = dm.get_custom_fields(lid)
        assert fields["cor"] == "branco"
        assert fields["garantia"] == "1 ano"

    def test_custom_fields_blank_key_ignored(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        dm.set_custom_fields(lid, {"": "vazio", "  ": "espacos", "valido": "ok"})
        fields = dm.get_custom_fields(lid)
        assert "valido" in fields
        # Chaves em branco devem ser ignoradas
        assert "" not in fields


class TestLocalDataManagerBatchOperations:
    """Testa operacoes batch otimizadas."""

    def _get_manager(self):
        from data_layer.local_data_manager import LocalDataManager
        return LocalDataManager()

    def test_delete_listings_batch_sql(self, mock_app_dirs, sample_listing_data, sample_listing_data_2):
        """Deletar em batch deve usar uma unica query."""
        dm = self._get_manager()
        lid1 = dm.create_listing(sample_listing_data, [])
        lid2 = dm.create_listing(sample_listing_data_2, [])
        count = dm.delete_listings([lid1, lid2])
        assert count == 2
        assert dm.get_all_listings() == []

    def test_delete_listings_empty_list(self, mock_app_dirs):
        dm = self._get_manager()
        assert dm.delete_listings([]) == 0

    def test_update_statuses_batch_sql(self, mock_app_dirs, sample_listing_data, sample_listing_data_2):
        """Atualizar status em batch deve usar uma unica query."""
        dm = self._get_manager()
        lid1 = dm.create_listing(sample_listing_data, [])
        lid2 = dm.create_listing(sample_listing_data_2, [])
        count = dm.update_statuses([lid1, lid2], "vendido")
        assert count == 2
        for lid in [lid1, lid2]:
            assert dm.get_listing(lid)["status"] == "vendido"

    def test_update_statuses_empty_list(self, mock_app_dirs):
        dm = self._get_manager()
        assert dm.update_statuses([], "pausado") == 0


class TestLocalDataManagerRepostInterval:
    """Testa intervalo de repostagem configuravel."""

    def _get_manager(self):
        from data_layer.local_data_manager import LocalDataManager
        return LocalDataManager()

    def test_custom_interval_3_days(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        quatro_dias_atras = (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d')
        dm.atualizar_apos_postagem(lid, quatro_dias_atras, "https://fb.com/item/1", True)
        # Com intervalo de 3 dias, deve repostar
        produtos = dm.get_produtos_para_repostar(interval_days=3)
        assert len(produtos) == 1

    def test_custom_interval_10_days(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        quatro_dias_atras = (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d')
        dm.atualizar_apos_postagem(lid, quatro_dias_atras, "https://fb.com/item/1", True)
        # Com intervalo de 10 dias, NAO deve repostar
        produtos = dm.get_produtos_para_repostar(interval_days=10)
        assert len(produtos) == 0

    def test_interval_from_env(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        cinco_dias_atras = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        dm.atualizar_apos_postagem(lid, cinco_dias_atras, "https://fb.com/item/1", True)
        os.environ["REPOST_INTERVAL_DAYS"] = "3"
        try:
            produtos = dm.get_produtos_para_repostar()
            assert len(produtos) == 1
        finally:
            os.environ.pop("REPOST_INTERVAL_DAYS", None)


class TestLocalDataManagerExportImport:
    """Testa export/import CSV e JSON."""

    def _get_manager(self):
        from data_layer.local_data_manager import LocalDataManager
        return LocalDataManager()

    def test_export_csv(self, mock_app_dirs, sample_listing_data, sample_listing_data_2, temp_dir):
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])
        dm.create_listing(sample_listing_data_2, [])

        csv_path = str(temp_dir / "export.csv")
        count = dm.export_to_csv(csv_path)
        assert count == 2
        assert Path(csv_path).exists()

        # Verificar conteudo
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        assert "iPhone 15 Pro Max 256GB" in content
        assert "MacBook Air M2 2023" in content

    def test_export_json(self, mock_app_dirs, sample_listing_data, temp_dir):
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])

        json_path = str(temp_dir / "export.json")
        count = dm.export_to_json(json_path)
        assert count == 1

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["titulo"] == "iPhone 15 Pro Max 256GB"

    def test_import_csv(self, mock_app_dirs, temp_dir):
        dm = self._get_manager()

        csv_path = temp_dir / "import.csv"
        csv_path.write_text(
            'titulo,preco,categoria,status\n'
            '"Produto CSV 1",100.00,"Eletronicos","ativo"\n'
            '"Produto CSV 2",200.00,"Moveis","pausado"\n',
            encoding='utf-8-sig',
        )

        imported, errors = dm.import_from_csv(str(csv_path))
        assert imported == 2
        assert errors == 0
        assert len(dm.get_all_listings()) == 2

    def test_import_json(self, mock_app_dirs, temp_dir):
        dm = self._get_manager()

        json_path = temp_dir / "import.json"
        data = [
            {"titulo": "Produto JSON 1", "preco": 300, "status": "ativo"},
            {"titulo": "Produto JSON 2", "preco": 400, "status": "vendido"},
        ]
        json_path.write_text(json.dumps(data), encoding='utf-8')

        imported, errors = dm.import_from_json(str(json_path))
        assert imported == 2
        assert errors == 0
        assert len(dm.get_all_listings()) == 2

    def test_roundtrip_csv(self, mock_app_dirs, sample_listing_data, temp_dir):
        """Export + Import deve preservar dados."""
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])

        csv_path = str(temp_dir / "roundtrip.csv")
        dm.export_to_csv(csv_path)

        # Limpar banco
        for l in dm.get_all_listings():
            dm.delete_listing(l["id"])
        assert len(dm.get_all_listings()) == 0

        # Re-importar
        imported, _ = dm.import_from_csv(csv_path)
        assert imported == 1
        listings = dm.get_all_listings()
        assert listings[0]["titulo"] == "iPhone 15 Pro Max 256GB"

    def test_roundtrip_json(self, mock_app_dirs, sample_listing_data, temp_dir):
        dm = self._get_manager()
        lid = dm.create_listing(sample_listing_data, [])
        dm.set_custom_fields(lid, {"cor": "preto"})

        json_path = str(temp_dir / "roundtrip.json")
        dm.export_to_json(json_path)

        for l in dm.get_all_listings():
            dm.delete_listing(l["id"])

        imported, _ = dm.import_from_json(json_path)
        assert imported == 1

    def test_import_csv_with_link(self, mock_app_dirs, temp_dir):
        dm = self._get_manager()
        csv_path = temp_dir / "with_link.csv"
        csv_path.write_text(
            'titulo,preco,link_anuncio,data_publicacao\n'
            '"Prod",100,"https://fb.com/item/1","2024-01-15"\n',
            encoding='utf-8-sig',
        )
        imported, _ = dm.import_from_csv(str(csv_path))
        assert imported == 1
        listings = dm.get_all_listings()
        assert listings[0]["link_anuncio"] == "https://fb.com/item/1"
        assert listings[0]["data_publicacao"] == "2024-01-15"


class TestLocalDataManagerBackup:
    """Testa backup do banco."""

    def _get_manager(self):
        from data_layer.local_data_manager import LocalDataManager
        return LocalDataManager()

    def test_backup_creates_file(self, mock_app_dirs, sample_listing_data, temp_dir):
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])

        backup_path = str(temp_dir / "backup_test.db")
        result = dm.backup_database(backup_path)
        assert result == backup_path
        assert Path(backup_path).exists()
        assert Path(backup_path).stat().st_size > 0

    def test_backup_default_location(self, mock_app_dirs, sample_listing_data):
        dm = self._get_manager()
        dm.create_listing(sample_listing_data, [])

        result = dm.backup_database()
        assert Path(result).exists()
        assert "backups" in result
        assert "reposter_" in Path(result).name
