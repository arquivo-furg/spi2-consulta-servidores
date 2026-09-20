CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- GiST apoia a similaridade por nome e a ordenação por distância (<->).
CREATE INDEX idx_servidor_nome_trgm
    ON servidor USING gin (nome gin_trgm_ops);

CREATE INDEX idx_cargo_descricao_trgm
    ON cargo USING gin (descricao gin_trgm_ops);

CREATE INDEX idx_orgao_nome_trgm
    ON orgao USING gin (nome gin_trgm_ops);

-- Índices das referências usadas nos filtros e JOINs da consulta.
CREATE INDEX idx_servidor_cargo_id
    ON servidor (cargo_id);

CREATE INDEX idx_servidor_orgao_id
    ON servidor (orgao_id);

CREATE INDEX idx_servidor_uf_sigla
    ON servidor (uf_sigla);
