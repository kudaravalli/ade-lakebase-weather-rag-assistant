CREATE INDEX IF NOT EXISTS idx_weather_embeddings_ann_hnsw
ON weather.weather_embeddings
USING hnsw
(
    embedding vector_cosine_ops
);

