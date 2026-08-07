"""
Databricks notebook:
sync_weather_documents.py

Purpose:

Synchronize weather data from the National Weather Service API
into Lakebase.

This notebook is called by:

resources/sync_weather_documents_job.yml


Flow:

Notebook
   |
   v
weather_sync.py
   |
   +--> Geocode locations
   |
   +--> Resolve NWS grid points
   |
   +--> Fetch alerts
   |
   +--> Fetch forecasts
   |
   +--> Normalize documents
   |
   +--> Upsert Lakebase


"""

from __future__ import annotations


import json
import logging
import os
import sys



# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO
)


logger = logging.getLogger(
    "sync-weather-documents"
)



# ----------------------------------------------------------------------
# Make project modules available
#
# When deployed with Databricks Asset Bundles,
# the repo root is mounted with the notebook.
# ----------------------------------------------------------------------

sys.path.append(
    os.path.abspath("..")
)



import lakebase


from weather_schema import (
    ensure_weather_schema,
)


from weather_sync import (
    sync_weather_documents,
)





# ----------------------------------------------------------------------
# Job parameters
# ----------------------------------------------------------------------

try:

    dbutils

except NameError:

    dbutils = None





def get_parameter(
    name: str,
    default: str,
):

    if dbutils:

        try:

            return dbutils.widgets.get(
                name
            )

        except Exception:

            pass


    return default





locations_json = get_parameter(
    "locations_json",
    """
    [
        "Chicago, IL",
        "Austin, TX",
        {"lat": 37.7749, "lon": -122.4194},
    ]
    """,
)



weather_table_name = get_parameter(
    "weather_table_name",
    "weather.weather_documents",
)



location_cache_table_name = get_parameter(
    "location_cache_table_name",
    "weather.location_cache",
)





# ----------------------------------------------------------------------
# Parse locations
# ----------------------------------------------------------------------

locations = json.loads(
    locations_json
)



logger.info(
    "Locations to sync: %s",
    locations,
)




# ----------------------------------------------------------------------
# Initialize schema
# ----------------------------------------------------------------------

ensure_weather_schema()





# ----------------------------------------------------------------------
# Run ingestion
#
# The sync function internally:
#
# - geocodes locations
# - caches locations
# - resolves NWS grids
# - fetches weather products
# - writes Lakebase documents
#
# ----------------------------------------------------------------------

synced_count = sync_weather_documents(
    locations=locations,
)




# ----------------------------------------------------------------------
# Output metrics
# ----------------------------------------------------------------------

result = {

    "weather_table":
        weather_table_name,


    "location_cache_table":
        location_cache_table_name,


    "locations_processed":
        len(locations),


    "documents_synced":
        synced_count,

}



logger.info(
    "Weather sync complete: %s",
    result,
)



print(
    json.dumps(
        result,
        indent=2,
    )
)

