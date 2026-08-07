"""
Databricks notebook:
ingest_weather_embeddings.py

Purpose:

Generate vector embeddings for weather documents
stored in Lakebase using psycopg2 and pgvector.

Input:

weather.weather_documents

Output:

weather.weather_embeddings

Designed for:

* Databricks Vector Search
* RAG applications
* Semantic weather search

Pipeline:

weather.weather_documents

```
    |
    v
```

Filter documents without embeddings

```
    |
    v
```

Chunk narrative_text

(CHUNK_SIZE=800,
CHUNK_OVERLAP=100)

```
    |
    v
```

Sentence Transformer

sentence-transformers/all-MiniLM-L6-v2

(384 dimensions)

```
    |
    v
```

weather.weather_embeddings

"""

from **future** import annotations

import hashlib
import json
import logging
import os
import sys

from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer

# ----------------------------------------------------------------------

# Logging

# ----------------------------------------------------------------------

logging.basicConfig(
level=logging.INFO
)

logger = logging.getLogger(
"weather-embeddings"
)

# ----------------------------------------------------------------------

# Project imports

# ----------------------------------------------------------------------

sys.path.append(
os.path.abspath("..")
)

import lakebase

# ----------------------------------------------------------------------

# Databricks notebook parameters

# ----------------------------------------------------------------------

try:
dbutils
except NameError:
dbutils = None

def get_parameter(
name,
default,
):
"""
Read Databricks notebook parameters.

```
Falls back to defaults when running locally.
"""

if dbutils:

    try:
        return dbutils.widgets.get(
            name
        )

    except Exception:
        pass

return default
```

# ----------------------------------------------------------------------

# Configuration

# ----------------------------------------------------------------------

WEATHER_TABLE = get_parameter(
"weather_table_name",
"weather.weather_documents",
)

EMBEDDINGS_TABLE = get_parameter(
"embeddings_table_name",
"weather.weather_embeddings",
)

MODEL_NAME = get_parameter(
"embedding_model",
"sentence-transformers/all-MiniLM-L6-v2",
)

EMBEDDING_DIMENSION = 384

CHUNK_SIZE = int(
get_parameter(
"chunk_size",
"800",
)
)

CHUNK_OVERLAP = int(
get_parameter(
"chunk_overlap",
"100",
)
)

MAX_DOCUMENTS = int(
get_parameter(
"max_documents_per_run",
"5000",
)
)

BATCH_SIZE = int(
get_parameter(
"batch_size",
"100",
)
)

# ----------------------------------------------------------------------

# Helpers

# ----------------------------------------------------------------------

def chunk_text(
text: str,
):
"""
Split document text using a sliding window.

```
Most weather documents are short,
but this handles longer alerts and
instruction text.
"""

if not text:
    return []


chunks = []

start = 0

length = len(text)


while start < length:

    end = min(
        start + CHUNK_SIZE,
        length,
    )


    chunks.append(
        text[start:end]
    )


    start += (
        CHUNK_SIZE
        -
        CHUNK_OVERLAP
    )


return chunks
```

def ensure_embedding_table():
"""
Create the embedding table if needed.

```
Note:
Production deployments should run
SQL migrations separately.

This exists only for development
convenience.
"""

lakebase.run_write(
    f"""
    CREATE TABLE IF NOT EXISTS {EMBEDDINGS_TABLE}
    (

        id TEXT PRIMARY KEY,

        document_id TEXT NOT NULL,

        chunk_index INTEGER NOT NULL,

        chunk_text TEXT NOT NULL,

        embedding VECTOR({EMBEDDING_DIMENSION}),

        model_name TEXT NOT NULL,

        created_at TIMESTAMPTZ
            DEFAULT now()

    )
    """
)
```

def load_documents():

```
"""
Load weather documents that may require embeddings.
"""

return lakebase.run_query(
    f"""
    SELECT

        id,

        narrative_text


    FROM {WEATHER_TABLE}


    ORDER BY synced_at DESC


    LIMIT %s

    """,
    (
        MAX_DOCUMENTS,
    ),
)
```

def embedding_id(
document_id,
chunk_index,
):
"""
Generate deterministic embedding IDs.

```
This allows safe reruns.
"""

value = (
    f"{document_id}:{chunk_index}"
)


return hashlib.md5(
    value.encode("utf-8")
).hexdigest()
```

def existing_embeddings(
document_ids,
):
"""
Retrieve existing document IDs
that already have embeddings.
"""

```
if not document_ids:
    return set()


rows = lakebase.run_query(
    f"""
    SELECT DISTINCT document_id

    FROM {EMBEDDINGS_TABLE}

    WHERE document_id = ANY(%s)

    """,
    (
        document_ids,
    ),
)


return {
    row["document_id"]
    for row in rows
}
```

"""
Databricks notebook:
ingest_weather_embeddings.py

Purpose:

Generate vector embeddings for weather documents
stored in Lakebase using psycopg2 and pgvector.

Input:

weather.weather_documents

Output:

weather.weather_embeddings

Designed for:

* Databricks Vector Search
* RAG applications
* Semantic weather search

Pipeline:

weather.weather_documents

```
    |
    v
```

Filter documents without embeddings

```
    |
    v
```

Chunk narrative_text

(CHUNK_SIZE=800,
CHUNK_OVERLAP=100)

```
    |
    v
```

Sentence Transformer

sentence-transformers/all-MiniLM-L6-v2

(384 dimensions)

```
    |
    v
```

weather.weather_embeddings

"""

from **future** import annotations

import hashlib
import json
import logging
import os
import sys

from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer

# ----------------------------------------------------------------------

# Logging

# ----------------------------------------------------------------------

logging.basicConfig(
level=logging.INFO
)

logger = logging.getLogger(
"weather-embeddings"
)

# ----------------------------------------------------------------------

# Project imports

# ----------------------------------------------------------------------

sys.path.append(
os.path.abspath("..")
)

import lakebase

# ----------------------------------------------------------------------

# Databricks notebook parameters

# ----------------------------------------------------------------------

try:
dbutils
except NameError:
dbutils = None

def get_parameter(
name,
default,
):
"""
Read Databricks notebook parameters.

```
Falls back to defaults when running locally.
"""

if dbutils:

    try:
        return dbutils.widgets.get(
            name
        )

    except Exception:
        pass

return default
```

# ----------------------------------------------------------------------

# Configuration

# ----------------------------------------------------------------------

WEATHER_TABLE = get_parameter(
"weather_table_name",
"weather.weather_documents",
)

EMBEDDINGS_TABLE = get_parameter(
"embeddings_table_name",
"weather.weather_embeddings",
)

MODEL_NAME = get_parameter(
"embedding_model",
"sentence-transformers/all-MiniLM-L6-v2",
)

EMBEDDING_DIMENSION = 384

CHUNK_SIZE = int(
get_parameter(
"chunk_size",
"800",
)
)

CHUNK_OVERLAP = int(
get_parameter(
"chunk_overlap",
"100",
)
)

MAX_DOCUMENTS = int(
get_parameter(
"max_documents_per_run",
"5000",
)
)

BATCH_SIZE = int(
get_parameter(
"batch_size",
"100",
)
)

# ----------------------------------------------------------------------

# Helpers

# ----------------------------------------------------------------------

def chunk_text(
text: str,
):
"""
Split document text using a sliding window.

```
Most weather documents are short,
but this handles longer alerts and
instruction text.
"""

if not text:
    return []


chunks = []

start = 0

length = len(text)


while start < length:

    end = min(
        start + CHUNK_SIZE,
        length,
    )


    chunks.append(
        text[start:end]
    )


    start += (
        CHUNK_SIZE
        -
        CHUNK_OVERLAP
    )


return chunks
```

def ensure_embedding_table():
"""
Create the embedding table if needed.

```
Note:
Production deployments should run
SQL migrations separately.

This exists only for development
convenience.
"""

lakebase.run_write(
    f"""
    CREATE TABLE IF NOT EXISTS {EMBEDDINGS_TABLE}
    (

        id TEXT PRIMARY KEY,

        document_id TEXT NOT NULL,

        chunk_index INTEGER NOT NULL,

        chunk_text TEXT NOT NULL,

        embedding VECTOR({EMBEDDING_DIMENSION}),

        model_name TEXT NOT NULL,

        created_at TIMESTAMPTZ
            DEFAULT now()

    )
    """
)
```

def load_documents():

```
"""
Load weather documents that may require embeddings.
"""

return lakebase.run_query(
    f"""
    SELECT

        id,

        narrative_text


    FROM {WEATHER_TABLE}


    ORDER BY synced_at DESC


    LIMIT %s

    """,
    (
        MAX_DOCUMENTS,
    ),
)
```

def embedding_id(
document_id,
chunk_index,
):
"""
Generate deterministic embedding IDs.

```
This allows safe reruns.
"""

value = (
    f"{document_id}:{chunk_index}"
)


return hashlib.md5(
    value.encode("utf-8")
).hexdigest()
```

def existing_embeddings(
document_ids,
):
"""
Retrieve existing document IDs
that already have embeddings.
"""

```
if not document_ids:
    return set()


rows = lakebase.run_query(
    f"""
    SELECT DISTINCT document_id

    FROM {EMBEDDINGS_TABLE}

    WHERE document_id = ANY(%s)

    """,
    (
        document_ids,
    ),
)


return {
    row["document_id"]
    for row in rows
}
```

```python
# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------

ensure_embedding_table()


logger.info(
    "Loading weather documents"
)


documents = load_documents()


logger.info(
    "Documents loaded: %s",
    len(documents),
)


if not documents:

    logger.info(
        "No documents found. Nothing to embed."
    )

    result = {
        "documents_processed": 0,
        "embeddings_created": 0,
        "model": MODEL_NAME,
    }

    print(
        json.dumps(
            result,
            indent=2,
        )
    )

    raise SystemExit(0)



document_ids = [
    document["id"]
    for document in documents
]


already_embedded = existing_embeddings(
    document_ids
)


logger.info(
    "Already embedded documents: %s",
    len(already_embedded),
)



logger.info(
    "Loading embedding model: %s",
    MODEL_NAME,
)


model = SentenceTransformer(
    MODEL_NAME
)


embedding_rows = []

documents_processed = 0


for document in documents:


    document_id = document["id"]


    if document_id in already_embedded:

        logger.info(
            "Skipping existing document: %s",
            document_id,
        )

        continue



    chunks = chunk_text(
        document.get(
            "narrative_text",
            "",
        )
    )


    if not chunks:

        logger.info(
            "Skipping empty document: %s",
            document_id,
        )

        continue



    logger.info(
        "Embedding document %s (%s chunks)",
        document_id,
        len(chunks),
    )


    vectors = model.encode(
        chunks,
        normalize_embeddings=True,
    )



    for index, vector in enumerate(vectors):


        embedding_rows.append(
            (
                embedding_id(
                    document_id,
                    index,
                ),

                document_id,

                index,

                chunks[index],

                vector.tolist(),

                MODEL_NAME,
            )
        )


    documents_processed += 1



logger.info(
    "Generated %s embeddings",
    len(embedding_rows),
)



# ----------------------------------------------------------------------
# Write embeddings using psycopg2
# ----------------------------------------------------------------------

if embedding_rows:


    insert_sql = f"""
        INSERT INTO {EMBEDDINGS_TABLE}
        (
            id,
            document_id,
            chunk_index,
            chunk_text,
            embedding,
            model_name,
            created_at
        )

        VALUES %s


        ON CONFLICT(id)

        DO UPDATE SET

            chunk_text =
                EXCLUDED.chunk_text,

            embedding =
                EXCLUDED.embedding,

            model_name =
                EXCLUDED.model_name,

            created_at =
                now()

    """



    with lakebase.get_connection() as conn:


        with conn.cursor() as cursor:


            batch = []


            for row in embedding_rows:


                batch.append(
                    row
                )


                if len(batch) >= BATCH_SIZE:


                    execute_values(
                        cursor,
                        insert_sql,
                        [
                            (
                                item[0],
                                item[1],
                                item[2],
                                item[3],
                                json.dumps(
                                    item[4]
                                ),
                                item[5],
                            )

                            for item in batch
                        ],
                        template="""
                        (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s::vector,
                            %s,
                            now()
                        )
                        """,
                    )


                    batch = []



            if batch:


                execute_values(
                    cursor,
                    insert_sql,
                    [
                        (
                            item[0],
                            item[1],
                            item[2],
                            item[3],
                            json.dumps(
                                item[4]
                            ),
                            item[5],
                        )

                        for item in batch
                    ],
                    template="""
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s::vector,
                        %s,
                        now()
                    )
                    """,
                )


        conn.commit()



else:


    logger.info(
        "No new embeddings generated"
    )



# ----------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------

result = {

    "documents_processed":
        documents_processed,


    "embeddings_created":
        len(embedding_rows),


    "model":
        MODEL_NAME,


    "embedding_dimension":
        EMBEDDING_DIMENSION,

}


logger.info(
    "Embedding ingestion complete: %s",
    result,
)


print(
    json.dumps(
        result,
        indent=2,
    )
)
```

