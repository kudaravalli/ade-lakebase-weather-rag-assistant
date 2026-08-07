"""
Lakebase schema definitions for the weather application.

Creates:

- weather_documents
    Normalized NWS weather documents.

- location_cache
    Cached location -> lat/lon -> NWS grid resolution.

- weather_embeddings
    Master embedding store.

- weather_alert_embeddings
    Alert-only embeddings for severe weather retrieval.

- weather_forecast_embeddings
    Forecast-only embeddings for forecast Q&A.
"""


import lakebase

WEATHER_SCHEMA = "weather"

WEATHER_DOCUMENTS_TABLE = (
    "weather.weather_documents"
)

LOCATION_CACHE_TABLE = (
    "weather.location_cache"
)

WEATHER_EMBEDDINGS_TABLE = (
    "weather.weather_embeddings"
)

WEATHER_ALERT_EMBEDDINGS_TABLE = (
    "weather.weather_alert_embeddings"
)

WEATHER_FORECAST_EMBEDDINGS_TABLE = (
    "weather.weather_forecast_embeddings"
)


def ensure_weather_schema():

    _create_weather_documents_table()

    _create_location_cache_table()

    _create_embedding_table(
        WEATHER_EMBEDDINGS_TABLE
    )

    _create_embedding_table(
        WEATHER_ALERT_EMBEDDINGS_TABLE
    )

    _create_embedding_table(
        WEATHER_FORECAST_EMBEDDINGS_TABLE
    )


def _create_weather_documents_table():

    lakebase.run_write(
        f"""
        CREATE TABLE IF NOT EXISTS
        {WEATHER_DOCUMENTS_TABLE}
        (

            id TEXT PRIMARY KEY,

            location TEXT NOT NULL,

            source_type TEXT NOT NULL
            CHECK
            (
              source_type IN
              (
                'alert',
                'forecast',
                'observation'
              )
            ),

            headline TEXT,

            narrative_text TEXT,

            content_hash TEXT,

            issued_at TIMESTAMPTZ,

            effective_at TIMESTAMPTZ,

            payload JSONB NOT NULL,

            synced_at TIMESTAMPTZ
                NOT NULL
                DEFAULT now()

        )
        """
    )


def _create_location_cache_table():

    lakebase.run_write(
        f"""
        CREATE TABLE IF NOT EXISTS
        {LOCATION_CACHE_TABLE}
        (

            location_key TEXT PRIMARY KEY,

            latitude DOUBLE PRECISION NOT NULL,

            longitude DOUBLE PRECISION NOT NULL,

            display_name TEXT,

            nws_office TEXT,

            nws_grid_x INTEGER,

            nws_grid_y INTEGER,

            payload JSONB,

            created_at TIMESTAMPTZ
                NOT NULL
                DEFAULT now(),

            updated_at TIMESTAMPTZ
                NOT NULL
                DEFAULT now()

        )
        """
    )


def _create_embedding_table(
    table_name: str
):

    lakebase.run_write(
        f"""
        CREATE TABLE IF NOT EXISTS
        {table_name}
        (

            id TEXT PRIMARY KEY,

            document_id TEXT NOT NULL,

            location TEXT,

            source_type TEXT,

            headline TEXT,

            chunk_text TEXT,

            content_hash TEXT,

            embedding JSONB NOT NULL,

            created_at TIMESTAMPTZ
                NOT NULL
                DEFAULT now()

        )
        """
    )

