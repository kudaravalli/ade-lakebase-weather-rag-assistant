# SQL Setup Files for Lakebase Weather Service

These SQL files must be run manually in your Lakebase PostgreSQL database before running the weather ingestion and embedding notebooks.

The setup creates all required database objects for the Databricks Weather Service application.

All application tables are created inside the `weather` schema.

Created objects:

- `weather.location_cache`
- `weather.weather_documents`
- `weather.weather_embeddings`

---

# Setup Order

Run the SQL files in the following order:

```
00_create_schema.sql
        |
        v
01_create_location_cache.sql
        |
        v
02_create_weather_documents.sql
        |
        v
03_create_embedding_tables.sql
        |
        v
04_create_indexes.sql
        |
        v
05_seed_default_locations.sql
```

---

# 1. Run `00_create_schema.sql`

Creates the application schema.

Creates:

```sql
weather
```

All application tables use fully qualified names:

```
weather.<table_name>
```

Examples:

```
weather.location_cache

weather.weather_documents
```

Using an explicit schema prevents accidental table creation in the PostgreSQL `public` schema.

---

# 2. Run `01_create_location_cache.sql`

Creates the location resolution cache.

The weather application accepts locations in either form.

## City / State

Example:

```
Chicago, IL
Austin, TX
```

## Latitude / Longitude

Example:

```json
{
  "latitude": 41.8781,
  "longitude": -87.6298
}
```

The application resolves locations through:

```
User Location
       |
       v
Latitude / Longitude
       |
       v
NWS /points API
       |
       v
Forecast Office + Grid Coordinates
```

The result is cached to avoid unnecessary API calls.

Creates:

```
weather.location_cache
```

Stores:

| Column | Description |
|---|---|
| location_key | Original user supplied location |
| latitude | Resolved latitude |
| longitude | Resolved longitude |
| display_name | Human readable location |
| nws_office | NWS forecast office |
| nws_grid_x | NWS grid X coordinate |
| nws_grid_y | NWS grid Y coordinate |
| payload | Raw API response |
| created_at | Creation timestamp |
| updated_at | Last update timestamp |

---

# 3. Run `02_create_weather_documents.sql`

Creates the primary weather document store.

Creates:

```
weather.weather_documents
```

This table stores normalized National Weather Service data.

Supported document types:

```
alert
forecast
```

Examples:

## Alert

```
Flash Flood Warning
Severe Thunderstorm Warning
Winter Storm Advisory
```

## Forecast

```
Today: Sunny, with a high near 75.
```

---

## Document Structure

| Column | Description |
|---|---|
| id | Stable document identifier |
| location | City/state or coordinates |
| source_type | alert or forecast |
| headline | Weather event title |
| narrative_text | Text used for embeddings |
| issued_at | Issue timestamp |
| effective_at | Effective timestamp |
| content_hash | Deduplication hash |
| payload | Original NWS JSON |
| synced_at | Lakebase sync timestamp |

---

# 4. Run `03_create_embedding_tables.sql`

Creates tables used by the embedding pipeline.

Creates:

```
weather.weather_embeddings
```

The embedding pipeline reads from:

```
weather.weather_documents
```

and writes generated embeddings into this table.

---

# Embedding Model Dimension

If using pgvector, replace:

```
{{EMBEDDING_DIM}}
```

with the correct embedding dimension for your model.

Recommended models:

| Model | Dimension |
|---|---:|
| sentence-transformers/all-MiniLM-L6-v2 | 384 |
| sentence-transformers/all-mpnet-base-v2 | 768 |
| BAAI/bge-small-en-v1.5 | 384 |
| BAAI/bge-base-en-v1.5 | 768 |
| BAAI/bge-large-en-v1.5 | 1024 |

Example:

For:

```
sentence-transformers/all-MiniLM-L6-v2
```

use:

```
384
```

---

# 5. Run `04_create_indexes.sql`

Creates indexes needed for application performance.

Indexes support:

## Location queries

```
weather.location_cache(location_key)
```

Used for:

- Cached geocoding
- NWS grid lookups

---

## Weather document searches

```
weather.weather_documents(location)

weather.weather_documents(source_type)

weather.weather_documents(synced_at)
```

Used for:

- Location filtering
- Alert filtering
- Forecast filtering
- Recent document retrieval

---

## Embedding lookups

```
weather.weather_embeddings(document_id)
```

Used during:

- Semantic search
- RAG retrieval
- Document enrichment

---

# 6. Run `05_seed_default_locations.sql`

Optional.

Adds sample locations for testing.

Default locations:

```
Chicago, IL

Austin, TX

Seattle, WA
```

This helps validate:

- Location cache creation
- NWS grid lookup
- Weather synchronization

The application still supports arbitrary locations through:

```
POST /weather/sync
```

Example:

```json
{
  "locations": [
    "Chicago, IL",
    "Austin, TX"
  ],
  "limit": 50
}
```

---

# Post-Processing After Notebook Execution

After running the weather embedding notebook, verify that embeddings were generated.

Run:

```sql
SELECT
    'weather.weather_embeddings' AS table_name,
    COUNT(*) AS records
FROM weather.weather_embeddings
```

Expected:

```
table_name                              records
------------------------------------------------
weather.weather_embeddings              N
```

---

# Why Manual Setup?

The Databricks notebooks use Spark JDBC for reliable execution.

Spark JDBC has limitations with PostgreSQL-specific features:

- Cannot reliably execute arbitrary DDL
- Cannot create PostgreSQL extensions
- Cannot create pgvector indexes
- Cannot always write directly to VECTOR columns
- Limited PostgreSQL upsert support

By creating the database objects manually:

You get:

- ✅ Proper Lakebase schema setup
- ✅ PostgreSQL-compatible tables
- ✅ Controlled index creation
- ✅ Stable Spark notebook execution
- ✅ Repeatable deployment process
- ✅ Separation of database setup and data processing

---

# Recommended Deployment Sequence

For a new environment:

```
1. Create Lakebase instance

        |
        v

2. Run SQL setup scripts

        |
        v

3. Deploy Databricks App

        |
        v

4. Trigger weather sync

        |
        v

5. Validate weather_documents

        |
        v

6. Run embedding notebook

        |
        v

7. Enable semantic search / RAG
```

---

# Verification Queries

## Verify Tables Exist

```sql
SELECT
    table_schema,
    table_name
FROM information_schema.tables
WHERE table_schema = 'weather'
ORDER BY table_name;
```

Expected:

```
weather
 |
 +-- location_cache
 |
 +-- weather_documents
 |
 +-- weather_embeddings
```

---

## Verify Weather Documents

```sql
SELECT
    location,
    source_type,
    headline,
    synced_at
FROM weather.weather_documents
ORDER BY synced_at DESC
LIMIT 20;
```

Example result:

```
Chicago, IL | alert    | Flood Warning
Austin, TX  | forecast | Sunny
```

---

## Verify Location Cache

```sql
SELECT
    location_key,
    latitude,
    longitude,
    nws_office
FROM weather.location_cache;
```

---

## Verify Embedding Generation

```sql
SELECT COUNT(*)
FROM weather.weather_embeddings;
```

---

# Cleanup

For development environments only.

Run:

```
99_cleanup.sql
```

This removes the complete weather schema:

```sql
DROP SCHEMA IF EXISTS weather CASCADE;
```

Do not run this in production.

---

# File Summary

| File | Purpose |
|---|---|
| `00_create_schema.sql` | Creates weather schema |
| `01_create_location_cache.sql` | Creates NWS/geocode cache |
| `02_create_weather_documents.sql` | Creates normalized weather document store |
| `03_create_embedding_tables.sql` | Creates embedding storage tables |
| `04_create_indexes.sql` | Creates query indexes |
| `05_seed_default_locations.sql` | Adds sample test locations |
| `99_cleanup.sql` | Removes development schema |

---

# Final Lakebase Layout

After setup:

```
Lakebase PostgreSQL

weather
│
├── location_cache
│
├── weather_documents
│
├── weather_embeddings
```

The application, notebooks, and Databricks jobs should reference these tables using fully qualified names:

```
weather.location_cache

weather.weather_documents

weather.weather_embeddings
```

