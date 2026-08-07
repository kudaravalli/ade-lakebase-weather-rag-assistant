# README_WEATHER.md

# Weather Service – Semantic Weather Search

This project extends the Databricks App sample into a semantic weather search application using **Lakebase**, **pgvector**, and **Sentence Transformers**. It ingests National Weather Service (NWS) weather forecasts and alerts, generates vector embeddings, and enables natural-language semantic search over the stored weather documents.

---

## Data Source

This project uses the **U.S. National Weather Service (NWS) API** (`https://api.weather.gov`) as its weather data source.

### Why the National Weather Service?

The NWS API was selected because it:

- Is the official weather API provided by the U.S. government.
- Does not require API keys or authentication.
- Provides high-quality forecasts, watches, warnings, and alerts.
- Returns structured JSON suitable for ingestion into Lakebase.
- Is free to use for educational and demonstration purposes.

The application currently retrieves:

- Forecasts
- Weather alerts and warnings

Each response is normalized into a common document format before being stored in Lakebase.

---

# Data Model

The application stores data in three primary tables.

## weather.location_cache

Caches geocoding results so repeated location lookups do not require additional API requests.

Example columns:

- location_name
- latitude
- longitude
- grid_x
- grid_y
- office
- updated_at

---

## weather.weather_documents

Stores normalized weather documents retrieved from the NWS API.

Key columns include:

- id
- location
- source_type (`forecast` or `alert`)
- headline
- narrative_text
- issued_at
- effective_at
- payload (raw JSON)
- synced_at

Each row represents a searchable weather document.

---

## weather.weather_embeddings

Stores vector embeddings generated from weather document text.

Columns:

- id
- document_id
- chunk_index
- chunk_text
- embedding (`VECTOR(384)`)
- model_name
- created_at

A pgvector HNSW index is created on the `embedding` column for efficient cosine similarity search.

---

# Embedding Strategy

This project uses the same embedding model as the Day-2 news application for consistency.

**Model**

```
sentence-transformers/all-MiniLM-L6-v2
```

Embedding dimension:

```
384
```

Using the same embedding model keeps the retrieval pipeline compatible with the existing semantic search implementation while providing good performance for short weather text.

---

# Chunking Strategy

Weather documents are chunked before embedding.

Configuration:

```
CHUNK_SIZE = 800 words
CHUNK_OVERLAP = 100 words
```

Most weather forecasts and alerts are relatively short and fit into a single chunk. The sliding-window chunking logic primarily benefits longer alert descriptions and instruction text while maintaining context across chunk boundaries.

---

# End-to-End Pipeline

The application consists of three major stages.

## 1. Sync Weather Data

The Databricks App retrieves forecasts and alerts from the National Weather Service and stores them in Lakebase.

```
POST /weather/sync
```

Example request:

```json
{
  "locations": [
    "Chicago, IL",
    "Austin, TX"
  ]
}
```

This populates:

```
weather.weather_documents
```

---

## 2. Generate Embeddings

Run the embedding pipeline:

```bash
python embedding/weather_embedding_pipeline.py
```

The pipeline:

- Reads documents that have not yet been embedded
- Splits long documents into chunks
- Generates sentence embeddings
- Writes vectors into

```
weather.weather_embeddings
```

using `psycopg2` and pgvector.

---

## 3. Semantic Search

Search the embedded weather documents using natural language.

Endpoint:

```
POST /weather/search
```

Example:

```json
{
  "query": "risk of flooding near rivers",
  "top_k": 5
}
```

The application:

1. Embeds the query using the same Sentence Transformer model.
2. Performs cosine similarity search using pgvector.
3. Returns the most relevant weather document chunks.

Example response:

```json
{
  "query": "risk of flooding near rivers",
  "count": 2,
  "results": [
    {
      "location": "Chicago, IL",
      "headline": "Flood Warning",
      "chunk_text": "...",
      "similarity": 0.92
    }
  ]
}
```

---

# Technologies Used

- Databricks Apps
- Lakebase (PostgreSQL)
- pgvector
- psycopg2
- Flask
- Sentence Transformers
- National Weather Service API

---

# Known Limitations

Current limitations include:

- The application currently supports only U.S. locations because it relies on the National Weather Service API.
- Weather data is refreshed on demand or through scheduled jobs rather than real-time streaming.
- Semantic search uses vector similarity only and does not combine keyword (hybrid) search.
- Weather forecasts naturally become stale and require periodic synchronization.
- Duplicate documents are minimized through upserts, but additional document versioning could be added.

---

# Optional features 

The application now supports:

- Idempotent weather ingestion
- Multiple weather sources
- Semantic filtering by source_type
- pgvector HNSW indexing
- Scheduled synchronization
- Optional RAG summaries

### Search Examples

All weather:

GET /weather/search?query=flood risk


Alerts only:

GET /weather/search?query=flood risk&source_type=alert


Forecast discussions:

GET /weather/search?query=heat wave&source_type=forecast


---


# Future Improvements

Given additional time, the following enhancements would be valuable:

- Hybrid search combining pgvector similarity with PostgreSQL full-text search.
- Automatic scheduled synchronization using Databricks Jobs.
- Retrieval-Augmented Generation (RAG) to generate natural-language weather summaries from retrieved documents.
- Metadata filtering by state, county, weather event type, or alert severity.
- Support for additional weather providers beyond the National Weather Service.
- Incremental embedding updates that process only modified documents.
- Re-ranking retrieved results using a cross-encoder model for improved relevance.

---

# Overall Architecture

```
National Weather Service API
            │
            ▼
      weather_client.py
            │
            ▼
     weather_sync.py
            │
            ▼
weather.weather_documents
            │
            ▼
weather_embedding_pipeline.py
            │
            ▼
weather.weather_embeddings
            │
            ▼
      POST /weather/search
            │
            ▼
      Semantic Weather Results
```

