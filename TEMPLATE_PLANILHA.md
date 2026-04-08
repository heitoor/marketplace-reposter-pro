# Formato de Dados - Marketplace Reposter Pro v3.x

> **NOTA:** A partir da v3.0, os dados sao armazenados em banco SQLite local.
> Este documento descreve o formato para import/export CSV/JSON.

## Colunas do banco de dados

| Campo | Tipo | Obrigatorio | Descricao |
|-------|------|-------------|-----------|
| titulo | texto | sim | Titulo do anuncio (max 200 chars) |
| preco | numero | sim | Preco em R$ (ex: 1500.00) |
| categoria | texto | nao | Categoria do produto |
| condicao | texto | nao | Novo, Usado - Bom, Usado - Como novo, etc |
| descricao | texto | nao | Descricao detalhada (max 5000 chars) |
| localizacao | texto | nao | Cidade, Estado (max 100 chars) |
| status | texto | nao | ativo, pausado, vendido (default: ativo) |
| link_anuncio | texto | nao | URL do anuncio no Facebook |
| data_publicacao | texto | nao | Data da ultima postagem (YYYY-MM-DD) |

## Exemplo CSV

```csv
titulo,preco,categoria,condicao,descricao,localizacao,status
"iPhone 15 Pro Max 256GB",5999.99,"Eletronicos","Usado - Bom","iPhone em otimo estado","Sao Paulo, SP","ativo"
"MacBook Air M2",8500.00,"Eletronicos","Novo","Lacrado na caixa","Rio de Janeiro, RJ","ativo"
```

## Exemplo JSON

```json
[
  {
    "titulo": "iPhone 15 Pro Max 256GB",
    "preco": 5999.99,
    "categoria": "Eletronicos",
    "condicao": "Usado - Bom",
    "descricao": "iPhone em otimo estado",
    "localizacao": "Sao Paulo, SP",
    "status": "ativo"
  }
]
```

## Status validos

- **ativo** - Sera repostado automaticamente
- **pausado** - Nao sera repostado
- **vendido** - Nao sera repostado

## Categorias comuns

- Eletronicos
- Moveis
- Veiculos
- Roupas e Acessorios
- Esportes e Lazer
- Casa e Jardim
- Brinquedos e Jogos
- Instrumentos Musicais
