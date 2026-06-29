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
from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AQIDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching AQI data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        self._aqi_client: AQIClient | None = None
        self._country = entry.data["country"]
        self._state = entry.data["state"]
        self._city = entry.data["city"]
        self.selected_sensors = entry.options.get("sensors", [])

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )

    async def _async_setup(self) -> None:
        """Set up the client."""
        if self._aqi_client is None:
            self._aqi_client = AQIClient()

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            await self._async_setup()
            assert self._aqi_client is not None
            
            # Get location data using the stored city slug
            location_data = await self._aqi_client.get_location_by_slug(self._city)
            
            if not location_data:
                raise UpdateFailed("No data available from API")
                
            return location_data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err