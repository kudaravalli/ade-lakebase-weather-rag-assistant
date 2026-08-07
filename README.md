# Weather Service – Databricks App with Lakebase and Semantic Search

A Databricks App that ingests weather forecasts and alerts from the U.S. National Weather Service (NWS), stores normalized weather documents in Lakebase (Databricks-managed PostgreSQL), generates vector embeddings using Sentence Transformers, and enables semantic weather search using pgvector.

This project is based on the Day-2 "The Rise of Data AI Engineer" sample application and adapts the same architecture for weather data.

---

# Features

- Flask REST API
- National Weather Service (NWS) weather ingestion
- Lakebase (PostgreSQL) persistence
- pgvector semantic search
- Sentence Transformers embeddings
- Databricks Apps deployment
- Databricks Asset Bundles support
- Scheduled embedding ingestion job
- Geocoding cache to minimize repeated API requests

---

# Project Architecture

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
          embedding/weather_embedding_pipeline.py
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

---

# Repository Structure

```
weather-service/
│
├── app.py
├── app.yaml
├── databricks.yml
├── lakebase.py
├── weather_client.py
├── weather_schema.py
├── weather_search.py
├── weather_sync.py
├── setup_secrets.py
├── requirements.txt
│
├── embedding/
│   ├── chunking.py
│   └── weather_embedding_pipeline.py
│
├── notebooks/
│   ├── ingest_weather_embeddings.py
│   └── weather_semantic_search_demo.py
│
├── sql/
│   ├── 00_create_schema.sql
│   ├── 01_create_location_cache.sql
│   ├── 02_create_weather_documents.sql
│   ├── 03_create_embedding_tables.sql
│   ├── 04_create_indexes.sql
│   ├── 05_seed_default_locations.sql
│   └── README.md
│
├── templates/
│   └── index.html
│
├── resources/
│   └── ingest_weather_embeddings_job.yml
│
├── README.md
└── README_WEATHER.md
```

---

# Additional Documentation

This repository includes supplemental documentation describing the weather ingestion and semantic search implementation.

| Document | Description |
|----------|-------------|
| **README.md** | Project overview, setup, deployment, API usage, and architecture. |
| **README_WEATHER.md** | Weather-specific implementation details, including the data source, schema design, chunking strategy, embedding model, semantic retrieval pipeline, and known limitations. |

For implementation details of the semantic search pipeline, refer to **README_WEATHER.md** after completing the project setup described in this document.

---

# Technology Stack

- Python 3.11
- Flask
- Databricks Apps
- Lakebase (PostgreSQL)
- pgvector
- psycopg2
- Sentence Transformers
- National Weather Service API
- Databricks Asset Bundles

---

# Prerequisites

- Databricks Workspace
- Databricks Apps enabled
- Lakebase instance
- Databricks CLI configured
- Python 3.11+

---

# Installation

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

---

# Configure Secrets

Run:

```bash
python setup_secrets.py
```

This creates the required Databricks secret scopes and stores your Lakebase connection information.

---

# Database Setup

Execute the SQL scripts in the following order:

```
sql/
├── 00_create_schema.sql
├── 01_create_location_cache.sql
├── 02_create_weather_documents.sql
├── 03_create_embedding_tables.sql
├── 04_create_indexes.sql
└── 05_seed_default_locations.sql
```

See **sql/README.md** for detailed instructions.

---

# Running the Application

Run locally:

```bash
python app.py
```

The application will start on:

```
http://localhost:8000
```

---

# API Endpoints

## Health Check

```
GET /healthz
```

Returns:

```json
{
  "status": "ok",
  "service": "weather-app"
}
```

---

## Sync Weather Data

```
POST /weather/sync
```

Example:

```json
{
  "locations": [
    "Chicago, IL",
    "Austin, TX"
  ]
}
```

---

## List Weather Documents

```
GET /weather/documents
```

Returns recently synchronized weather documents.

---

## Semantic Weather Search

```
POST /weather/search
```

Example request:

```json
{
  "query": "risk of flooding near rivers",
  "top_k": 5
}
```

Example response:

```json
{
  "query": "risk of flooding near rivers",
  "count": 5,
  "results": [
    {
      "location": "Chicago, IL",
      "headline": "Flood Warning",
      "chunk_text": "...",
      "similarity": 0.93
    }
  ]
}
```

For additional implementation details—including schema decisions, chunking strategy, embedding generation, and retrieval workflow—see **README_WEATHER.md**.

---

# Embedding Pipeline

Generate vector embeddings by running:

```bash
python embedding/weather_embedding_pipeline.py
```

The pipeline:

1. Reads unembedded weather documents
2. Chunks long narratives
3. Generates embeddings
4. Writes vectors into pgvector tables

---

# Databricks Deployment

Deploy the application:

```bash
databricks bundle deploy
```

Run the embedding job:

```bash
databricks bundle run ingest_weather_embeddings_job
```

---

# Configuration

Important environment variables include:

| Variable | Default |
|----------|---------|
| WEATHER_TABLE_NAME | weather.weather_documents |
| LOCATION_CACHE_TABLE_NAME | weather.location_cache |
| WEATHER_LOCATIONS_JSON | Built-in defaults |

---

# Future Improvements

Potential enhancements include:

- Hybrid keyword + vector search
- Cross-encoder reranking
- Retrieval-Augmented Generation (RAG)
- Streaming weather updates
- Additional weather providers
- Metadata-based filtering
- Incremental embedding refreshes

---

# License

This project is intended for educational purposes as part of a Databricks weather semantic search demonstration.

