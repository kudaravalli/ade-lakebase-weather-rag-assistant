"""
Weather semantic search utilities.

Uses:
    sentence-transformers/all-MiniLM-L6-v2

Embedding dimension:
    384

Database:
    Lakebase PostgreSQL + pgvector

Search:
    cosine similarity using pgvector <=> operator
"""

import logging
import os

from sentence_transformers import SentenceTransformer

import lakebase


logger = logging.getLogger(
    "weather-search"
)


MODEL_NAME = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)


MODEL = None



def load_embedding_model():

    """
    Explicitly load the embedding model.

    This should be called once during
    application startup.

    Keeping the model in memory avoids
    loading the transformer model for
    every request.
    """

    global MODEL


    if MODEL is None:

        logger.info(
            "Initializing embedding model: %s",
            MODEL_NAME,
        )


        MODEL = SentenceTransformer(
            MODEL_NAME
        )


        logger.info(
            "Embedding model loaded successfully"
        )


    return MODEL



def get_embedding_model():

    """
    Retrieve the already loaded model.

    If the application was started
    without warm-up (for example,
    running a standalone script),
    this safely initializes it lazily.
    """

    if MODEL is None:

        return load_embedding_model()


    return MODEL



def embed_query(
    query: str
) -> list[float]:

    model = get_embedding_model()

    vector = model.encode(
        query,
        normalize_embeddings=True,
    )

    return vector.tolist()



def search_weather_documents(
    query_embedding: list[float],
    top_k: int = 5,
):

    sql = """
    SELECT

        d.id,

        d.location,

        d.headline,

        d.narrative_text,

        d.source_type,

        e.chunk_text,

        1 - (
            e.embedding <=> %s::vector
        ) AS similarity


    FROM weather.weather_embeddings e


    JOIN weather.weather_documents d

        ON d.id = e.document_id


    WHERE

        (%s IS NULL OR d.source_type=%s)


    ORDER BY

        e.embedding <=> %s::vector


    LIMIT %s;

    """


    vector_string = str(
        query_embedding
    )


    with lakebase.get_connection() as conn:

        with conn.cursor(
        ) as cur:

            cur.execute(
                sql,
                (
                    vector_string,
                    vector_string,
                    top_k,
                ),
            )

            rows = cur.fetchall()


    return rows

