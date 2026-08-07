CREATE INDEX IF NOT EXISTS idx_weather_location_cache_key
ON weather.location_cache(location_key);

CREATE INDEX IF NOT EXISTS idx_weather_documents_location
ON weather.weather_documents(location);

CREATE INDEX IF NOT EXISTS idx_weather_documents_source_type
ON weather.weather_documents(source_type);

CREATE INDEX IF NOT EXISTS idx_weather_documents_synced
ON weather.weather_documents(synced_at DESC);

CREATE INDEX IF NOT EXISTS idx_weather_documents_hash
ON weather.weather_documents(content_hash);

CREATE INDEX IF NOT EXISTS idx_weather_embeddings_document
ON weather.weather_embeddings(document_id);

CREATE INDEX IF NOT EXISTS idx_weather_embeddings_source_type
ON weather.weather_embeddings(source_type);

