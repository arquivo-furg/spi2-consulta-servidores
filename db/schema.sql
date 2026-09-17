CREATE TABLE cargo (
    id BIGINT PRIMARY KEY,
    descricao TEXT NOT NULL
);

CREATE TABLE orgao (
    id BIGINT PRIMARY KEY,
    nome TEXT NOT NULL
);

CREATE TABLE uf (
    sigla VARCHAR(2) PRIMARY KEY
);

-- Cargo e órgão ficam em tabelas próprias para não repetir seus textos em cada servidor.
-- uf_sigla aceita NULL porque a fonte de aposentados não informa esse campo.
CREATE TABLE servidor (
    id BIGINT PRIMARY KEY,
    nome TEXT NOT NULL,
    cargo_id BIGINT NOT NULL REFERENCES cargo (id),
    orgao_id BIGINT NOT NULL REFERENCES orgao (id),
    uf_sigla VARCHAR(2) REFERENCES uf (sigla)
);
