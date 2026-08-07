EXPLAIN ANALYZE

SELECT

id,

document_id


FROM weather.weather_embeddings


ORDER BY

embedding <=> '[0,0,0]'::vector


LIMIT 5;

