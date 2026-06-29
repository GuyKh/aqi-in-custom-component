"""The aqi_in integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from aqi_in_api import AQIClient

from .const import DOMAIN
from .coordinator import AQIDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up aqi_in from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Share one AQIClient across all config entries
    if "client" not in hass.data[DOMAIN]:
        client = await hass.async_add_executor_job(AQIClient)
        hass.data[DOMAIN]["client"] = client
    else:
        client = hass.data[DOMAIN]["client"]

    coordinator = AQIDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

        # Close the shared client when the last entry is removed
        active_entries = [k for k in hass.data[DOMAIN] if k != "client"]
        if not active_entries:
            client = hass.data[DOMAIN].pop("client", None)
            if client:
                await client.close()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
