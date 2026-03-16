"""
Local Data Manager - Substitui GoogleSheetsManager.
Gerencia anuncios via SQLite + imagens locais.
"""

import logging
import uuid
from datetime import datetime, timedelta

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


class LocalDataManager:
    """Gerencia dados de anuncios usando SQLite + imagens locais."""

    def __init__(self):
        self.db = Database()
        self.image_manager = ImageManager()
        logger.info("Conectado ao banco de dados local")
        print("Conectado ao banco de dados local!")

    # ===== Interface compativel com o Reposter =====

    def get_produtos_para_repostar(self) -> list:
        """Busca anuncios ativos que precisam ser repostados (>7 dias)."""
        print("Carregando anuncios do banco de dados...")

        sete_dias_atras = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        rows = self.db.fetchall("""
            SELECT * FROM listings
            WHERE status = 'ativo'
            AND (data_publicacao = '' OR data_publicacao IS NULL OR data_publicacao <= ?)
            ORDER BY data_publicacao ASC
        """, (sete_dias_atras,))

        produtos = []
        for row in rows:
            produto = {}
            for col, key in _COLUMN_TO_KEY.items():
                produto[key] = row[col] if row[col] is not None else ''
            produtos.append(produto)

        total = self.db.fetchone("SELECT COUNT(*) as cnt FROM listings WHERE status = 'ativo'")
        total_count = total['cnt'] if total else 0

        print(f"Total de anuncios ativos: {total_count}")
        print(f"Anuncios para repostar (>7 dias): {len(produtos)}\n")

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
            # Padronizar formato da data para YYYY-MM-DD
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
        # Padronizar formato da data para YYYY-MM-DD
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

        # Salvar imagens
        if image_paths:
            self.image_manager.add_images(listing_id, image_paths)

        # Salvar campos customizados
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

            # Atualizar imagens se fornecidas
            if image_paths is not None:
                self.image_manager.replace_images(listing_id, image_paths)

            # Atualizar campos customizados
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
        """Deleta multiplos anuncios."""
        count = 0
        for lid in listing_ids:
            if self.delete_listing(lid):
                count += 1
        return count

    def update_status(self, listing_id: str, new_status: str) -> bool:
        """Altera status de um anuncio."""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.db.execute(
            "UPDATE listings SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, listing_id)
        )
        return True

    def update_statuses(self, listing_ids: list, new_status: str) -> int:
        """Altera status de multiplos anuncios."""
        count = 0
        for lid in listing_ids:
            if self.update_status(lid, new_status):
                count += 1
        return count

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
        # Escapar caracteres especiais do LIKE
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
