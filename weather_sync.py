"""
Weather synchronization pipeline.

Responsibilities:

- Resolve locations into coordinates.
- Cache geocoding results.
- Resolve NWS grid points.
- Fetch weather alerts and forecast discussions.
- Normalize API responses into weather_documents.
- Upsert into Lakebase.

This module is intentionally independent of Flask so it can be used by:

- app.py endpoint
- Databricks notebooks
- scheduled jobs
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

import requests

import lakebase

from weather_client import WeatherClient


logger = logging.getLogger(
    "weather-sync"
)


WEATHER_TABLE_NAME = "weather_documents"

LOCATION_CACHE_TABLE_NAME = "location_cache"



# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------


def sync_weather_documents(
    locations: list[Any],
    limit: int = 50,
) -> int:
    """
    Main weather ingestion function.

    Input examples:

    [
        "Chicago, IL",

        {
            "lat": 41.8781,
            "lon": -87.6298
        }
    ]

    Returns:

        Number of documents synced.
    """

    client = WeatherClient()

    documents = []


    for location in locations:

        try:

            resolved = resolve_location(
                location
            )


            grid = resolve_nws_grid(
                client,
                resolved
            )


            alerts = client.get_active_alerts()


            for alert in alerts[:limit]:

                documents.append(
                    normalize_alert(
                        location,
                        alert,
                    )
                )


            forecasts = client.get_forecast(
                office=grid["office"],
                grid_x=grid["grid_x"],
                grid_y=grid["grid_y"],
            )


            for period in (
                forecasts
                .get("properties", {})
                .get("periods", [])
                [:limit]
            ):

                documents.append(
                    normalize_forecast(
                        location,
                        period,
                    )
                )


        except Exception:

            logger.exception(
                "Failed syncing location %s",
                location,
            )


    return upsert_weather_documents(
        documents
    )



# ----------------------------------------------------------------------
# Location resolution
# ----------------------------------------------------------------------


def resolve_location(
    location: Any,
) -> dict:
    """
    Resolve input location into coordinates.

    Supports:

    "Chicago, IL"

    OR

    {
        "lat": 41.8,
        "lon": -87.6
    }
    """


    if isinstance(
        location,
        dict,
    ):

        return {

            "display_name": (
                location.get(
                    "name"
                )
                or
                f'{location["lat"]},{location["lon"]}'
            ),

            "latitude":
                location["lat"],

            "longitude":
                location["lon"],
        }



    if isinstance(
        location,
        str,
    ):

        cached = get_cached_location(
            location
        )

        if cached:

            return cached



        coordinates = geocode_location(
            location
        )


        save_location_cache(
            location,
            coordinates,
        )


        return coordinates



    raise ValueError(
        f"Unsupported location: {location}"
    )



# ----------------------------------------------------------------------
# Geocoding
# ----------------------------------------------------------------------


def geocode_location(
    location: str,
) -> dict:
    """
    Uses OpenStreetMap Nominatim.

    No API key required.

    """

    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": location,
            "format": "json",
            "limit": 1,
        },
        headers={
            "User-Agent":
                "ade-lakebase-weather-rag-assistant"
        },
        timeout=30,
    )


    response.raise_for_status()


    results = response.json()


    if not results:

        raise ValueError(
            f"Unable to geocode {location}"
        )


    result = results[0]


    return {

        "display_name":
            result.get(
                "display_name",
                location,
            ),

        "latitude":
            float(result["lat"]),

        "longitude":
            float(result["lon"]),

    }



# ----------------------------------------------------------------------
# Location cache
# ----------------------------------------------------------------------


def get_cached_location(
    location_key: str,
) -> dict | None:


    rows = lakebase.run_query(
        """
        SELECT
            location_key,
            display_name,
            latitude,
            longitude
        FROM location_cache
        WHERE location_key = %s
        """,
        (
            location_key,
        ),
    )


    if not rows:

        return None


    row = rows[0]


    return {

        "display_name":
            row["display_name"],

        "latitude":
            row["latitude"],

        "longitude":
            row["longitude"],

    }



def save_location_cache(
    location_key: str,
    location: dict,
):

    lakebase.run_write(
        """
        INSERT INTO location_cache
        (
            location_key,
            latitude,
            longitude,
            display_name,
            updated_at
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            now()
        )

        ON CONFLICT(location_key)
        DO UPDATE SET

            latitude =
                EXCLUDED.latitude,

            longitude =
                EXCLUDED.longitude,

            display_name =
                EXCLUDED.display_name,

            updated_at =
                now()

        """,
        (
            location_key,
            location["latitude"],
            location["longitude"],
            location["display_name"],
        ),
    )



# ----------------------------------------------------------------------
# NWS grid resolution
# ----------------------------------------------------------------------


def resolve_nws_grid(
    client: WeatherClient,
    location: dict,
):

    return client.resolve_grid_point(
        location["latitude"],
        location["longitude"],
    )



# ----------------------------------------------------------------------
# Normalization
# ----------------------------------------------------------------------


def normalize_alert(
    location,
    alert: dict,
) -> dict:


    properties = (
        alert.get(
            "properties",
            {}
        )
    )


    narrative = (
        properties.get(
            "description"
        )
        or
        properties.get(
            "instruction"
        )
        or ""
    )


    return build_document(
        location=location,
        source_type="alert",
        headline=(
            properties.get(
                "event"
            )
        ),
        narrative=narrative,
        issued_at=(
            properties.get(
                "sent"
            )
        ),
        effective_at=(
            properties.get(
                "effective"
            )
        ),
        payload=alert,
    )



def normalize_forecast(
    location,
    forecast: dict,
) -> dict:


    return build_document(
        location=location,
        source_type="forecast",
        headline=(
            forecast.get(
                "name"
            )
        ),
        narrative=(
            forecast.get(
                "detailedForecast",
                ""
            )
        ),
        issued_at=None,
        effective_at=None,
        payload=forecast,
    )



def build_document(
    location,
    source_type,
    headline,
    narrative,
    issued_at,
    effective_at,
    payload,
):

    raw = json.dumps(
        payload,
        sort_keys=True,
    )


    content_hash = hashlib.md5(
        raw.encode(
            "utf-8"
        )
    ).hexdigest()


    if isinstance(
        location,
        str,
    ):

        location_value = location

    else:

        location_value = (
            f'{location["lat"]},'
            f'{location["lon"]}'
        )


    return {

        "id":
            hashlib.md5(
                (
                    location_value
                    +
                    source_type
                    +
                    content_hash
                )
                .encode()
            )
            .hexdigest(),


        "location":
            location_value,


        "source_type":
            source_type,


        "headline":
            headline,


        "narrative_text":
            narrative,


        "content_hash":
            content_hash,


        "issued_at":
            issued_at,


        "effective_at":
            effective_at,


        "payload":
            payload,


        "synced_at":
            datetime.now(
                timezone.utc
            ),

    }



# ----------------------------------------------------------------------
# Lakebase persistence
# ----------------------------------------------------------------------


def upsert_weather_documents(
    documents: list[dict],
) -> int:


    count = 0


    with lakebase.get_connection() as conn:

        with conn.cursor() as cur:


            for document in documents:


                cur.execute(
                    """
                    INSERT INTO weather_documents
                    (
                        id,
                        location,
                        source_type,
                        headline,
                        narrative_text,
                        content_hash,
                        issued_at,
                        effective_at,
                        payload,
                        synced_at
                    )

                    VALUES
                    (
                        %s,%s,%s,%s,%s,
                        %s,%s,%s,%s,now()
                    )


                    ON CONFLICT(id)

                    DO UPDATE SET

                        headline =
                            EXCLUDED.headline,

                        narrative_text =
                            EXCLUDED.narrative_text,

                        content_hash =
                            EXCLUDED.content_hash,

                        payload =
                            EXCLUDED.payload,

                        synced_at =
                            now()

                    """,

                    (
                        document["id"],
                        document["location"],
                        document["source_type"],
                        document["headline"],
                        document["narrative_text"],
                        document["content_hash"],
                        document["issued_at"],
                        document["effective_at"],
                        json.dumps(
                            document["payload"]
                        ),
                    ),
                )


                count += 1


        conn.commit()


    return count

