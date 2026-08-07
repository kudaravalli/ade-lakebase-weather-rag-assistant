"""
Weather document embedding pipeline.

Reads:
    weather.weather_documents

Writes:
    weather.weather_embeddings

Uses:
    sentence-transformers/all-MiniLM-L6-v2

Embedding dimension:
    384

Database:
    Lakebase PostgreSQL + pgvector

Important:
    Uses psycopg2 only.
    Does not use Spark JDBC.
"""

import json
import logging
import os
from datetime import datetime, timezone

from sentence_transformers import SentenceTransformer
from psycopg2.extras import execute_values

import lakebase

from embedding.chunking import chunk_text


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(
    "weather-embedding"
)


MODEL_NAME = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)


EMBEDDING_DIM = 384


CHUNK_SIZE = int(
    os.getenv(
        "CHUNK_SIZE",
        "800"
    )
)


CHUNK_OVERLAP = int(
    os.getenv(
        "CHUNK_OVERLAP",
        "100"
    )
)


BATCH_SIZE = int(
    os.getenv(
        "BATCH_SIZE",
        "100"
    )
)


SOURCE_TABLE = (
    "weather.weather_documents"
)


TARGET_TABLE = (
    "weather.weather_embeddings"
)



def load_model():

    logger.info(
        "Loading embedding model %s",
        MODEL_NAME,
    )

    return SentenceTransformer(
        MODEL_NAME
    )



def get_unembedded_documents():

    sql = f"""
    SELECT
        d.id,
        d.location,
        d.source_type,
        d.headline,
        d.narrative_text

    FROM {SOURCE_TABLE} d

    LEFT JOIN {TARGET_TABLE} e
        ON d.id = e.document_id

    WHERE e.document_id IS NULL

    ORDER BY d.synced_at
    """


    with lakebase.get_connection() as conn:

        with conn.cursor(
        ) as cur:

            cur.execute(sql)

            rows = cur.fetchall()


    return rows



def create_chunks(documents):

    output = []


    for doc in documents:

        document_id = doc["id"]

        text = (
            doc["narrative_text"]
            or ""
        )


        chunks = chunk_text(
            text,
            CHUNK_SIZE,
            CHUNK_OVERLAP,
        )


        for index, chunk in enumerate(chunks):

            output.append(
                {
                    "id":
                        f"{document_id}-{index}",

                    "document_id":
                        document_id,

                    "chunk_index":
                        index,

                    "chunk_text":
                        chunk,
                }
            )


    return output



def generate_embeddings(
    chunks,
    model
):

    texts = [
        c["chunk_text"]
        for c in chunks
    ]


    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=BATCH_SIZE,
    )


    for item, vector in zip(
        chunks,
        vectors,
    ):

        item["embedding"] = (
            vector.tolist()
        )


    return chunks



def write_embeddings(rows):

    sql = f"""

    INSERT INTO {TARGET_TABLE}
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
            EXCLUDED.model_name

    """


    values = []


    for row in rows:

        values.append(
            (
                row["id"],
                row["document_id"],
                row["chunk_index"],
                row["chunk_text"],
                str(
                    row["embedding"]
                ),
                MODEL_NAME,
                datetime.now(
                    timezone.utc
                ),
            )
        )


    with lakebase.get_connection() as conn:

        with conn.cursor() as cur:

            execute_values(
                cur,
                sql,
                values,
                template="""
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s::vector,
                    %s,
                    %s
                )
                """
            )


        conn.commit()



def run():

    logger.info(
        "Reading weather documents"
    )


    documents = (
        get_unembedded_documents()
    )


    if not documents:

        logger.info(
            "No new documents"
        )

        return 0


    logger.info(
        "Documents found: %s",
        len(documents),
    )


    chunks = create_chunks(
        documents
    )


    logger.info(
        "Chunks generated: %s",
        len(chunks),
    )


    model = load_model()


    chunks = generate_embeddings(
        chunks,
        model,
    )


    write_embeddings(
        chunks
    )


    logger.info(
        "Inserted %s embeddings",
        len(chunks),
    )


    return len(chunks)



if __name__ == "__main__":

    count = run()

    print(
        {
            "embedded": count
        }
    )

