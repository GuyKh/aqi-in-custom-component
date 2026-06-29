"""Config flow for aqi_in integration."""

from __future__ import annotations

import logging
import math
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from aqi_in_api import AQIClient
from .const import CONF_SLUG, DOMAIN

_LOGGER = logging.getLogger(__name__)

ALL_LOCATIONS_URL = "https://apiserver.aqi.in/aqi/getAllMapLocations"
ALL_LOCATIONS_PARAMS: dict[str, str] = {"sensorname": "aqi", "source": "web"}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in km between two lat/lon points."""

    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _slug_to_label(slug: str) -> str:
    """Convert 'india/maharashtra/mumbai' to 'Mumbai, Maharashtra, India'."""
    parts = slug.split("/")
    if len(parts) >= 3:
        return "{}, {}, {}".format(
            parts[2].replace("-", " ").title(),
            parts[1].replace("-", " ").title(),
            parts[0].replace("-", " ").title(),
        )
    return slug.replace("-", " ").title()


async def _fetch_nearby_cities(
    hass: HomeAssistant,
) -> list[tuple[str, str]]:
    """Fetch all map locations and return top 50 nearest city slugs sorted by distance."""
    ha_lat: float = hass.config.latitude or 20.0
    ha_lon: float = hass.config.longitude or 77.0

    client = await hass.async_add_executor_job(AQIClient)
    try:
        token = await client._get_token()
        resp = await client._http.get(
            ALL_LOCATIONS_URL,
            params=ALL_LOCATIONS_PARAMS,
            headers={"authorization": f"bearer {token}"},
        )
        resp.raise_for_status()
        locations: list[dict[str, Any]] = resp.json().get("Locations", [])
    finally:
        await client.close()

    city_map: dict[str, dict[str, Any]] = {}
    for loc in locations:
        slug: str = loc.get("slug", "")
        parts = slug.split("/")
        if len(parts) < 3:
            continue
        city_slug = "/".join(parts[:3])
        dist = _haversine(ha_lat, ha_lon, loc.get("lat", 0), loc.get("lon", 0))
        entry = city_map.get(city_slug)
        if entry is None or dist < entry["_dist"]:
            city_map[city_slug] = {"slug": city_slug, "_dist": dist}

    sorted_cities = sorted(city_map.values(), key=lambda c: c["_dist"])
    return [(c["slug"], _slug_to_label(c["slug"])) for c in sorted_cities[:50]]


class AQIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            slug: str = user_input[CONF_SLUG]
            label = _slug_to_label(slug)
            await self.async_set_unique_id(slug)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=label,
                data={CONF_SLUG: slug},
            )

        errors: dict[str, str] = {}
        options: list[SelectOptionDict] = []

        try:
            nearby = await _fetch_nearby_cities(self.hass)
            options = [
                SelectOptionDict(value=slug, label=label) for slug, label in nearby
            ]
        except Exception:
            _LOGGER.exception("Failed to fetch nearby cities")
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SLUG): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self.async_step_user(user_input)
