"""DataUpdateCoordinator for the aqi_in integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from aqi_in_api import AQIClient
from .const import CONF_SLUG, DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AQIDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching AQI data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        aqi_client: AQIClient,
    ) -> None:
        """Initialize."""
        self._aqi_client = aqi_client
        self._slug = entry.data[CONF_SLUG]

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )

    @property
    def slug(self) -> str:
        """Return the configured location slug."""
        return self._slug

    async def _async_update_data(self) -> object:
        """Fetch data from API endpoint."""
        try:
            location_data = await self._aqi_client.get_location_by_slug(slug=self._slug)

            if not location_data:
                raise UpdateFailed("No data available from API")

            return location_data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
