"""
Client wrapper for the National Weather Service (NWS) API.

Responsibilities:

- Provides a thin HTTP client abstraction.
- Resolves coordinates to NWS grid points.
- Fetches active weather alerts.
- Fetches forecast discussions.
- Handles common NWS API headers.

The NWS API does not require an API key.

Documentation:
https://www.weather.gov/documentation/services-web-api
"""

from __future__ import annotations

import os
from typing import Any

import requests


_DEFAULT_BASE_URL = "https://api.weather.gov"

_DEFAULT_TIMEOUT = 30


_USER_AGENT = os.environ.get(
    "NWS_USER_AGENT",
    "ade-lakebase-weather-rag-assistant"
)


class WeatherClient:
    """
    Thin wrapper around the National Weather Service API.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = _DEFAULT_TIMEOUT,
    ):

        self.base_url = (
            base_url or _DEFAULT_BASE_URL
        ).rstrip("/")

        self.timeout = timeout

        self._session = requests.Session()

        self._session.headers.update(
            {
                "User-Agent": _USER_AGENT,
                "Accept": "application/geo+json",
            }
        )


    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict:

        response = self._session.get(
            f"{self.base_url}{path}",
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response.json()



    def get_points(
        self,
        latitude: float,
        longitude: float,
    ) -> dict:
        """
        Resolve a latitude/longitude pair into
        an NWS grid point.

        Endpoint:

            GET /points/{lat},{lon}

        Returns:

        {
            properties:
                {
                    gridId,
                    gridX,
                    gridY,
                    forecast,
                    forecastGridData
                }
        }
        """

        return self.get(
            f"/points/{latitude},{longitude}"
        )



    def get_active_alerts(
        self,
        area: str | None = None,
    ) -> list[dict]:
        """
        Fetch active NWS alerts.

        Endpoint:

            GET /alerts/active

        Optional filters:

            area=IL
            area=TX

        Returns:

            List of alert features.
        """

        params = {}

        if area:
            params["area"] = area


        data = self.get(
            "/alerts/active",
            params=params,
        )


        return (
            data.get(
                "features",
                []
            )
        )



    def get_forecast(
        self,
        office: str,
        grid_x: int,
        grid_y: int,
    ) -> dict:
        """
        Fetch standard forecast periods.

        Endpoint:

            GET /gridpoints/{office}/{x},{y}/forecast
        """

        return self.get(
            f"/gridpoints/"
            f"{office}/"
            f"{grid_x},{grid_y}"
            f"/forecast"
        )



    def get_forecast_discussions(
        self,
        office: str | None = None,
    ) -> list[dict]:
        """
        Fetch forecast discussion products.

        Forecast discussions are stored as
        NWS text products.

        Endpoint:

            GET /products/types/AFD

        Optionally filter by issuing office.
        """

        params = {
            "type": "AFD",
        }


        if office:
            params["location"] = office


        data = self.get(
            "/products",
            params=params,
        )

        return (
            data.get(
                "@graph",
                []
            )
        )



    def resolve_grid_point(
        self,
        latitude: float,
        longitude: float,
    ) -> dict:

        """
        Convenience helper.

        Returns normalized grid information:

        {
            latitude,
            longitude,
            office,
            grid_x,
            grid_y,
            forecast_url,
            forecast_grid_url
        }
        """

        data = self.get_points(
            latitude,
            longitude,
        )


        properties = (
            data.get(
                "properties",
                {}
            )
        )


        return {

            "latitude": latitude,

            "longitude": longitude,

            "office": properties.get(
                "gridId"
            ),

            "grid_x": properties.get(
                "gridX"
            ),

            "grid_y": properties.get(
                "gridY"
            ),

            "forecast_url": properties.get(
                "forecast"
            ),

            "forecast_grid_url": properties.get(
                "forecastGridData"
            ),

            "payload": data,

        }

