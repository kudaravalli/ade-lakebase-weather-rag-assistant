CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS weather.weather_embeddings (

    id TEXT PRIMARY KEY,

    document_id TEXT NOT NULL,

    chunk_index INTEGER NOT NULL,

    chunk_text TEXT NOT NULL,

    embedding VECTOR(384) NOT NULL,

    model_name TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_weather_embedding_document
        FOREIGN KEY(document_id)
        REFERENCES weather.weather_documents(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_weather_embedding_chunk
        UNIQUE(document_id, chunk_index)

);

