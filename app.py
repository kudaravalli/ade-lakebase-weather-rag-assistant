"""
Databricks Weather Service App

Provides:

- Flask REST API
- Lakebase persistence
- National Weather Service ingestion
- Weather document synchronization
- Semantic weather search using pgvector embeddings

Run locally:

    python app.py

Deploy using Databricks Apps with app.yaml.
"""

from __future__ import annotations

import json
import logging
import os

from flask import (
    Flask,
    jsonify,
    request,
    render_template,
)

from databricks.sdk import WorkspaceClient

import lakebase

from weather_schema import (
    ensure_weather_schema,
)

from weather_sync import (
    sync_weather_documents,
)

from weather_search import (
    embed_query,
    search_weather_documents,
    load_embedding_model,
)


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(
    "weather-app"
)


# ----------------------------------------------------------------------
# Flask initialization
# ----------------------------------------------------------------------

app = Flask(
    __name__
)

_w = WorkspaceClient()

# Load ML model during application startup.
initialize_application()


# ----------------------------------------------------------------------
# Application startup initialization
# ----------------------------------------------------------------------

def initialize_application():

    """
    Perform one-time application initialization.

    Currently:
        - Loads the sentence-transformer model into memory.

    Future additions could include:
        - Database connectivity validation
        - Schema validation
        - Health checks
    """

    try:

        logger.info(
            "Initializing Weather Service application"
        )


        # Load embedding model once.
        #
        # Without this, the first call to:
        #
        # POST /weather/search
        #
        # would pay the model initialization
        # cost.
        load_embedding_model()


        logger.info(
            "Weather Service initialization complete"
        )


    except Exception:

        logger.exception(
            "Application initialization failed"
        )


        raise


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

WEATHER_TABLE_NAME = os.environ.get(
    "WEATHER_TABLE_NAME",
    "weather.weather_documents",
)


LOCATION_CACHE_TABLE_NAME = os.environ.get(
    "LOCATION_CACHE_TABLE_NAME",
    "weather.location_cache",
)


# ----------------------------------------------------------------------
# Default locations
#
# Similar pattern to DEFAULT_NEWS_TICKERS
#
# Supports:
#
# "Chicago, IL"
#
# {
#     "lat": 41.8781,
#     "lon": -87.6298
# }
#
# ----------------------------------------------------------------------

DEFAULT_WEATHER_LOCATIONS = [

    "Chicago, IL",

    "Austin, TX",

    {
        "lat": 37.7749,
        "lon": -122.4194,
    },

]


def _load_default_locations():

    configured = os.environ.get(
        "WEATHER_LOCATIONS_JSON"
    )

    if not configured:

        return DEFAULT_WEATHER_LOCATIONS


    try:

        locations = json.loads(
            configured
        )


        if isinstance(
            locations,
            list,
        ):

            return locations


    except Exception:

        logger.exception(
            "Invalid WEATHER_LOCATIONS_JSON"
        )


    return DEFAULT_WEATHER_LOCATIONS



# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------

@app.route(
    "/healthz"
)
def healthz():

    return jsonify(
        {
            "status": "ok",
            "service": "weather-app",
        }
    )



@app.route(
    "/"
)
def index():

    return render_template(
        "index.html"
    )



@app.errorhandler(
    Exception
)
def handle_exception(
    error
):

    logger.exception(
        "Unhandled application error"
    )


    status = getattr(
        error,
        "code",
        500,
    )


    if not isinstance(
        status,
        int,
    ):

        status = 500


    return jsonify(
        {
            "error":
                str(error)
        }
    ), status



# ----------------------------------------------------------------------
# Weather synchronization
# ----------------------------------------------------------------------

@app.route(
    "/weather/sync",
    methods=[
        "POST"
    ],
)
def sync_weather():

    ensure_weather_schema()


    body = (
        request.json
        if request.is_json
        else {}
    )


    locations = (
        body.get(
            "locations"
        )
        or
        _load_default_locations()
    )


    limit = int(
        body.get(
            "limit",
            50,
        )
    )


    if not isinstance(
        locations,
        list,
    ):

        return jsonify(
            {
                "error":
                    "locations must be a list"
            }
        ), 400



    logger.info(
        "Syncing weather for %s",
        locations,
    )


    synced = sync_weather_documents(
        locations=locations,
        limit=limit,
    )


    return jsonify(
        {
            "synced":
                synced,

            "locations":
                locations,

        }
    )



# ----------------------------------------------------------------------
# Semantic weather search
# ----------------------------------------------------------------------

@app.route(
    "/weather/search",
    methods=[
        "POST"
    ],
)
def weather_search():

    """
    Semantic search over weather embeddings.

    Request:

    {
        "query":
            "risk of flooding near rivers",

        "top_k":
            5
    }


    Returns:

    {
        "query": "...",

        "count": 5,

        "results": [
            {
                "location": "...",
                "headline": "...",
                "chunk_text": "...",
                "similarity": 0.92
            }
        ]
    }

    """

    if not request.is_json:

        return jsonify(
            {
                "error":
                    "JSON body required"
            }
        ), 400



    body = request.json or {}


    query = body.get(
        "query"
    )


    if (
        not isinstance(
            query,
            str,
        )
        or not query.strip()
    ):

        return jsonify(
            {
                "error":
                    "query is required"
            }
        ), 400



    query = query.strip()



    top_k = body.get(
        "top_k",
        5,
    )


    try:

        top_k = int(
            top_k
        )

    except Exception:

        top_k = 5



    # Clamp retrieval size

    top_k = max(
        1,
        min(
            top_k,
            20,
        )
    )


    try:

        query_embedding = embed_query(
            query
        )


        rows = search_weather_documents(
            query_embedding,
            top_k,
        )


    except Exception:

        logger.exception(
            "Weather semantic search failed"
        )

        return jsonify(
            {
                "error":
                    "Search failed"
            }
        ), 500



    results = []


    for row in rows:

        results.append(
            {
                "location":
                    row["location"],

                "headline":
                    row["headline"],

                "chunk_text":
                    row["chunk_text"],

                "similarity":
                    float(
                        row["similarity"]
                    ),
            }
        )



    return jsonify(
        {
            "query":
                query,

            "count":
                len(results),

            "results":
                results,
        }
    )


@app.route(
    "/weather/search",
    methods=["GET"]
)
def weather_search():

    query = request.args.get(
        "query"
    )

    if not query:
        return jsonify(
            {
                "error":
                "query parameter required"
            }
        ),400


    top_k = int(
        request.args.get(
            "top_k",
            5
        )
    )


    source_type = request.args.get(
        "source_type"
    )


    results = search_weather_documents(
        query=query,
        top_k=top_k,
        source_type=source_type,
    )


    return jsonify(
        {
            "query": query,
            "results": results,
        }
    )


# ----------------------------------------------------------------------
# Query documents
# ----------------------------------------------------------------------

@app.route(
    "/weather/documents",
    methods=[
        "GET"
    ],
)
def weather_documents():

    ensure_weather_schema()


    limit = int(
        request.args.get(
            "limit",
            100,
        )
    )


    rows = lakebase.run_query(
        f"""
        SELECT

            id,

            location,

            source_type,

            headline,

            narrative_text,

            issued_at,

            effective_at,

            synced_at

        FROM {WEATHER_TABLE_NAME}

        ORDER BY synced_at DESC

        LIMIT %s

        """,
        (
            limit,
        ),
    )


    return jsonify(
        rows
    )



# ----------------------------------------------------------------------
# Application startup
# ----------------------------------------------------------------------

if __name__ == "__main__":

    # --------------------------------------------------------------
    # Warm up application dependencies before accepting requests.
    #
    # This loads:
    #   sentence-transformers/all-MiniLM-L6-v2
    #
    # once instead of during the first user search.
    # --------------------------------------------------------------

    initialize_application()


    host = os.getenv(
        "FLASK_RUN_HOST",
        "0.0.0.0",
    )


    port = int(
        os.getenv(
            "FLASK_RUN_PORT",
            "8000",
        )
    )


    app.run(
        debug=True,
        host=host,
        port=port,
    )

