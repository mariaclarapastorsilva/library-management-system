-- Executado a cada inicialização: todas as instruções são idempotentes.
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    prontuario  TEXT NOT NULL UNIQUE,
    nome        TEXT NOT NULL,
    curso       TEXT NOT NULL,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS maquinas (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    identificador  TEXT NOT NULL UNIQUE,          -- hostname enviado pelo cliente
    descricao      TEXT NOT NULL DEFAULT '',
    ativa          INTEGER NOT NULL DEFAULT 1,
    criado_em      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS sessoes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
    maquina_id  INTEGER NOT NULL REFERENCES maquinas(id),
    entrada     TEXT NOT NULL,                    -- 'AAAA-MM-DD HH:MM:SS'
    saida       TEXT                              -- NULL enquanto a sessão está aberta
);

CREATE INDEX IF NOT EXISTS idx_sessoes_abertas ON sessoes(maquina_id) WHERE saida IS NULL;
CREATE INDEX IF NOT EXISTS idx_sessoes_entrada ON sessoes(entrada);

CREATE TABLE IF NOT EXISTS administradores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario     TEXT NOT NULL UNIQUE,
    senha_hash  TEXT NOT NULL,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
