"""
Local Data Manager - Substitui GoogleSheetsManager.
Gerencia anuncios via SQLite + imagens locais.
"""

import csv
import io
import json
import logging
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from data_layer.database import Database
from data_layer.image_manager import ImageManager

logger = logging.getLogger(__name__)


# Mapeamento DB columns -> chaves acentuadas usadas pelo MarketplaceReposter
_COLUMN_TO_KEY = {
    'id': 'id',
    'titulo': 'Título',
    'preco': 'Preço',
    'categoria': 'Categoria',
    'condicao': 'Condição',
    'descricao': 'Descrição',
    'localizacao': 'Localização',
    'link_anuncio': 'Link Anúncio Atual',
    'data_publicacao': 'Data Publicação',
    'status': 'Status',
}

# Intervalo padrao para repostagem (dias)
DEFAULT_REPOST_INTERVAL_DAYS = 7


class LocalDataManager:
    """Gerencia dados de anuncios usando SQLite + imagens locais."""

    def __init__(self):
        self.db = Database()
        self.image_manager = ImageManager()
        logger.info("Conectado ao banco de dados local")
        print("Conectado ao banco de dados local!")

    def close(self):
        """Fecha conexao com o banco."""
        if self.db:
            self.db.close()

    # ===== Interface compativel com o Reposter =====

    def get_produtos_para_repostar(self, interval_days=None) -> list:
        """Busca anuncios ativos que precisam ser repostados.

        Args:
            interval_days: Dias desde ultima postagem para repostar.
                           None = usa REPOST_INTERVAL_DAYS do env ou default 7.
        """
        import os
        if interval_days is None:
            interval_days = int(os.getenv('REPOST_INTERVAL_DAYS', DEFAULT_REPOST_INTERVAL_DAYS))

        print("Carregando anuncios do banco de dados...")

        data_limite = (datetime.now() - timedelta(days=interval_days)).strftime('%Y-%m-%d')

        rows = self.db.fetchall("""
            SELECT * FROM listings
            WHERE status = 'ativo'
            AND (data_publicacao = '' OR data_publicacao IS NULL OR data_publicacao <= ?)
            ORDER BY data_publicacao ASC
        """, (data_limite,))

        produtos = []
        for row in rows:
            produto = {}
            for col, key in _COLUMN_TO_KEY.items():
                produto[key] = row[col] if row[col] is not None else ''
            produtos.append(produto)

        total = self.db.fetchone("SELECT COUNT(*) as cnt FROM listings WHERE status = 'ativo'")
        total_count = total['cnt'] if total else 0

        print(f"Total de anuncios ativos: {total_count}")
        print(f"Anuncios para repostar (>{interval_days} dias): {len(produtos)}\n")

        return produtos

    def get_imagens(self, produto: dict) -> list:
        """Retorna caminhos das imagens locais do anuncio."""
        listing_id = produto.get('id', '')
        if not listing_id:
            return []

        imagens = self.image_manager.get_images(listing_id)
        if imagens:
            print(f"  {len(imagens)} imagens encontradas")
        else:
            print("  Nenhuma imagem encontrada")
            logger.warning("Nenhuma imagem para listing %s", listing_id)
        return imagens

    def atualizar_apos_postagem(self, produto_id: str, data_publicacao: str,
                                 link_anuncio: str, sucesso: bool) -> bool:
        """Atualiza anuncio apos postagem."""
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if data_publicacao and len(data_publicacao) > 10:
                data_publicacao = data_publicacao[:10]
            if sucesso:
                self.db.execute("""
                    UPDATE listings
                    SET data_publicacao = ?, link_anuncio = ?,
                        post_count = post_count + 1, updated_at = ?
                    WHERE id = ?
                """, (data_publicacao, link_anuncio, now, produto_id))
                print("  Banco de dados atualizado")
            else:
                self.db.execute("""
                    UPDATE listings SET updated_at = ? WHERE id = ?
                """, (now, produto_id))
            return True
        except Exception as e:
            logger.error("Erro ao atualizar banco apos postagem: %s", e, exc_info=True)
            print(f"  ERRO ao atualizar banco: {e}")
            return False

    def update_link_and_date(self, listing_id: str, link: str, data_publicacao: str):
        """Atualiza link do anuncio e data de publicacao."""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if data_publicacao and len(data_publicacao) > 10:
            data_publicacao = data_publicacao[:10]
        self.db.execute("""
            UPDATE listings
            SET link_anuncio = ?, data_publicacao = ?, updated_at = ?
            WHERE id = ?
        """, (link, data_publicacao, now, listing_id))

    def limpar_temp_images(self):
        """Nao necessario para imagens locais (permanentes)."""
        pass

    # ===== CRUD para a GUI =====

    def get_all_listings(self) -> list:
        """Retorna todos os anuncios para exibicao na tabela."""
        rows = self.db.fetchall("""
            SELECT id, titulo, preco, categoria, condicao, localizacao,
                   status, data_publicacao, post_count, link_anuncio
            FROM listings
            ORDER BY updated_at DESC
        """)
        return [dict(row) for row in rows]

    def get_listing(self, listing_id: str) -> dict:
        """Retorna anuncio completo com campos customizados e imagens."""
        row = self.db.fetchone("SELECT * FROM listings WHERE id = ?", (listing_id,))
        if not row:
            return None

        listing = dict(row)
        listing['custom_fields'] = self.get_custom_fields(listing_id)
        listing['images'] = self.image_manager.get_images(listing_id)
        return listing

    def create_listing(self, data: dict, image_paths: list) -> str:
        """Cria novo anuncio. Retorna ID."""
        listing_id = str(uuid.uuid4())
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.db.execute("""
            INSERT INTO listings (id, titulo, preco, categoria, condicao,
                                  descricao, localizacao, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            listing_id,
            data.get('titulo', ''),
            float(data.get('preco', 0)),
            data.get('categoria', ''),
            data.get('condicao', 'Novo'),
            data.get('descricao', ''),
            data.get('localizacao', ''),
            data.get('status', 'ativo'),
            now, now,
        ))

        if image_paths:
            self.image_manager.add_images(listing_id, image_paths)

        custom_fields = data.get('custom_fields', {})
        if custom_fields:
            self.set_custom_fields(listing_id, custom_fields)

        return listing_id

    def update_listing(self, listing_id: str, data: dict, image_paths: list = None) -> bool:
        """Atualiza anuncio existente."""
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            self.db.execute("""
                UPDATE listings
                SET titulo = ?, preco = ?, categoria = ?, condicao = ?,
                    descricao = ?, localizacao = ?, status = ?, updated_at = ?
                WHERE id = ?
            """, (
                data.get('titulo', ''),
                float(data.get('preco', 0)),
                data.get('categoria', ''),
                data.get('condicao', 'Novo'),
                data.get('descricao', ''),
                data.get('localizacao', ''),
                data.get('status', 'ativo'),
                now, listing_id,
            ))

            if image_paths is not None:
                self.image_manager.replace_images(listing_id, image_paths)

            custom_fields = data.get('custom_fields', {})
            self.set_custom_fields(listing_id, custom_fields)

            return True
        except Exception as e:
            logger.error("Erro ao atualizar anuncio: %s", e, exc_info=True)
            print(f"Erro ao atualizar anuncio: {e}")
            return False

    def delete_listing(self, listing_id: str) -> bool:
        """Deleta anuncio, campos customizados e imagens."""
        try:
            self.db.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
            self.image_manager.delete_listing_images(listing_id)
            return True
        except Exception as e:
            logger.error("Erro ao deletar listing %s: %s", listing_id, e, exc_info=True)
            print(f"Erro ao deletar: {e}")
            return False

    def delete_listings(self, listing_ids: list) -> int:
        """Deleta multiplos anuncios em batch."""
        if not listing_ids:
            return 0
        placeholders = ','.join('?' for _ in listing_ids)
        try:
            self.db.execute(
                f"DELETE FROM listings WHERE id IN ({placeholders})",
                tuple(listing_ids)
            )
            for lid in listing_ids:
                self.image_manager.delete_listing_images(lid)
            return len(listing_ids)
        except Exception as e:
            logger.error("Erro ao deletar listings em batch: %s", e, exc_info=True)
            return 0

    def update_status(self, listing_id: str, new_status: str) -> bool:
        """Altera status de um anuncio."""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.db.execute(
            "UPDATE listings SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, listing_id)
        )
        return True

    def update_statuses(self, listing_ids: list, new_status: str) -> int:
        """Altera status de multiplos anuncios em batch."""
        if not listing_ids:
            return 0
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        placeholders = ','.join('?' for _ in listing_ids)
        self.db.execute(
            f"UPDATE listings SET status = ?, updated_at = ? WHERE id IN ({placeholders})",
            (new_status, now, *listing_ids)
        )
        return len(listing_ids)

    # ===== Custom Fields =====

    def get_custom_fields(self, listing_id: str) -> dict:
        """Retorna campos customizados como dict."""
        rows = self.db.fetchall(
            "SELECT field_key, field_value FROM custom_fields WHERE listing_id = ?",
            (listing_id,)
        )
        return {row['field_key']: row['field_value'] for row in rows}

    def set_custom_fields(self, listing_id: str, fields: dict):
        """Substitui todos os campos customizados."""
        self.db.execute("DELETE FROM custom_fields WHERE listing_id = ?", (listing_id,))
        if fields:
            params = [(listing_id, k, v) for k, v in fields.items() if k.strip()]
            if params:
                self.db.executemany(
                    "INSERT INTO custom_fields (listing_id, field_key, field_value) VALUES (?, ?, ?)",
                    params
                )

    def search_listings(self, query: str) -> list:
        """Busca anuncios por titulo, categoria ou descricao."""
        escaped = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        like = f"%{escaped}%"
        rows = self.db.fetchall("""
            SELECT id, titulo, preco, categoria, condicao, localizacao,
                   status, data_publicacao, post_count, link_anuncio
            FROM listings
            WHERE titulo LIKE ? ESCAPE '\\' OR categoria LIKE ? ESCAPE '\\'
               OR descricao LIKE ? ESCAPE '\\' OR localizacao LIKE ? ESCAPE '\\'
            ORDER BY updated_at DESC
        """, (like, like, like, like))
        return [dict(row) for row in rows]

    # ===== Backup =====

    def backup_database(self, dest_path: str = None) -> str:
        """Cria backup do banco de dados.

        Args:
            dest_path: Caminho destino. None = AppData/backups/reposter_YYYYMMDD_HHMMSS.db

        Returns:
            Caminho do backup criado.
        """
        from gui.utils.paths import get_data_dir
        if dest_path is None:
            backup_dir = get_data_dir() / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest_path = str(backup_dir / f"reposter_{timestamp}.db")

        shutil.copy2(str(self.db.DB_PATH), dest_path)
        logger.info("Backup criado em: %s", dest_path)
        return dest_path

    # ===== Export/Import =====

    def export_to_csv(self, file_path: str) -> int:
        """Exporta todos os listings para CSV.

        Returns:
            Numero de registros exportados.
        """
        rows = self.db.fetchall("""
            SELECT id, titulo, preco, categoria, condicao, descricao,
                   localizacao, status, link_anuncio, data_publicacao, post_count
            FROM listings ORDER BY updated_at DESC
        """)

        fieldnames = ['id', 'titulo', 'preco', 'categoria', 'condicao',
                       'descricao', 'localizacao', 'status', 'link_anuncio',
                       'data_publicacao', 'post_count']

        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))

        logger.info("Exportados %d listings para %s", len(rows), file_path)
        return len(rows)

    def export_to_json(self, file_path: str) -> int:
        """Exporta todos os listings para JSON.

        Returns:
            Numero de registros exportados.
        """
        rows = self.db.fetchall("""
            SELECT id, titulo, preco, categoria, condicao, descricao,
                   localizacao, status, link_anuncio, data_publicacao, post_count
            FROM listings ORDER BY updated_at DESC
        """)

        data = []
        for row in rows:
            listing = dict(row)
            listing['custom_fields'] = self.get_custom_fields(listing['id'])
            listing['images'] = self.image_manager.get_images(listing['id'])
            data.append(listing)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info("Exportados %d listings para %s", len(data), file_path)
        return len(data)

    def import_from_csv(self, file_path: str) -> tuple:
        """Importa listings de CSV.

        Returns:
            Tupla (importados, erros).
        """
        imported = 0
        errors = 0

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_data in reader:
                try:
                    data = {
                        'titulo': row_data.get('titulo', ''),
                        'preco': row_data.get('preco', 0),
                        'categoria': row_data.get('categoria', ''),
                        'condicao': row_data.get('condicao', 'Novo'),
                        'descricao': row_data.get('descricao', ''),
                        'localizacao': row_data.get('localizacao', ''),
                        'status': row_data.get('status', 'ativo'),
                    }
                    lid = self.create_listing(data, [])
                    # Se tiver link e data, atualizar
                    link = row_data.get('link_anuncio', '')
                    data_pub = row_data.get('data_publicacao', '')
                    if link or data_pub:
                        self.update_link_and_date(lid, link, data_pub)
                    imported += 1
                except Exception as e:
                    logger.warning("Erro ao importar linha CSV: %s", e)
                    errors += 1

        logger.info("CSV importado: %d OK, %d erros", imported, errors)
        return imported, errors

    def import_from_json(self, file_path: str) -> tuple:
        """Importa listings de JSON.

        Returns:
            Tupla (importados, erros).
        """
        imported = 0
        errors = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            data = [data]

        for item in data:
            try:
                listing_data = {
                    'titulo': item.get('titulo', ''),
                    'preco': item.get('preco', 0),
                    'categoria': item.get('categoria', ''),
                    'condicao': item.get('condicao', 'Novo'),
                    'descricao': item.get('descricao', ''),
                    'localizacao': item.get('localizacao', ''),
                    'status': item.get('status', 'ativo'),
                    'custom_fields': item.get('custom_fields', {}),
                }
                lid = self.create_listing(listing_data, [])
                link = item.get('link_anuncio', '')
                data_pub = item.get('data_publicacao', '')
                if link or data_pub:
                    self.update_link_and_date(lid, link, data_pub)
                imported += 1
            except Exception as e:
                logger.warning("Erro ao importar item JSON: %s", e)
                errors += 1

        logger.info("JSON importado: %d OK, %d erros", imported, errors)
        return imported, errors
