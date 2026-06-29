"""Config flow for aqi_in integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from aqi_in_api import AQIClient
from .const import (
    CONF_COUNTRY,
    CONF_CITY,
    CONF_STATE,
    CONF_SENSORS,
    DEFAULT_NAME,
    DOMAIN,
    SENSOR_TYPES,
)

ALL_SENSORS = list(SENSOR_TYPES.keys())


async def _get_aqi_client(hass: HomeAssistant) -> AQIClient:
    """Create an AQIClient in an executor to avoid blocking the event loop."""
    return await hass.async_add_executor_job(AQIClient)


def _country_selector(countries: list[dict[str, str]]) -> SelectSelector:
    """Build a dropdown selector for countries."""
    return SelectSelector(
        SelectSelectorConfig(
            options=[
                SelectOptionDict(value=c["code"], label=c["name"])
                for c in countries
            ],
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


def _state_selector(states: list[dict[str, str]]) -> SelectSelector:
    """Build a dropdown selector for states."""
    return SelectSelector(
        SelectSelectorConfig(
            options=[
                SelectOptionDict(value=s["code"], label=s["name"])
                for s in states
            ],
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


def _city_selector(cities: list[dict[str, str]]) -> SelectSelector:
    """Build a dropdown selector for cities."""
    return SelectSelector(
        SelectSelectorConfig(
            options=[
                SelectOptionDict(value=c["slug"], label=c["name"])
                for c in cities
            ],
            mode=SelectSelectorMode.DROPDOWN,
        )
    )



class AQIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for aqi_in."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._aqi_client: AQIClient | None = None
        self._country: str | None = None
        self._state: str | None = None
        self._city: str | None = None

    async def _ensure_client(self) -> AQIClient:
        """Ensure we have an AQIClient, creating one in executor if needed."""
        if self._aqi_client is None:
            self._aqi_client = await _get_aqi_client(self.hass)
        return self._aqi_client

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        return await self.async_step_country()

    async def async_step_country(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the country selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._country = user_input[CONF_COUNTRY]
            return await self.async_step_state()

        try:
            client = await self._ensure_client()
            countries = await client.get_countries()
        except Exception:
            errors["base"] = "cannot_fetch_countries"
            countries = []

        if not countries:
            countries = [
                {"code": "IN", "name": "India"},
                {"code": "US", "name": "United States"},
                {"code": "GB", "name": "United Kingdom"},
                {"code": "CA", "name": "Canada"},
                {"code": "AU", "name": "Australia"},
            ]

        return self.async_show_form(
            step_id="country",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COUNTRY): _country_selector(countries),
                }
            ),
            errors=errors,
        )

    async def async_step_state(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the state selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._state = user_input[CONF_STATE]
            return await self.async_step_city()

        try:
            client = await self._ensure_client()
            states = await client.get_states(self._country)
        except Exception:
            errors["base"] = "cannot_fetch_states"
            states = []

        if not states:
            states_map = {
                "IN": [
                    {"code": "DL", "name": "Delhi"},
                    {"code": "MH", "name": "Maharashtra"},
                    {"code": "KA", "name": "Karnataka"},
                    {"code": "TN", "name": "Tamil Nadu"},
                ],
                "US": [
                    {"code": "CA", "name": "California"},
                    {"code": "TX", "name": "Texas"},
                    {"code": "NY", "name": "New York"},
                    {"code": "FL", "name": "Florida"},
                ],
            }
            states = states_map.get(self._country, [])

        return self.async_show_form(
            step_id="state",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATE): _state_selector(states),
                }
            ),
            errors=errors,
        )

    async def async_step_city(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the city selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._city = user_input[CONF_CITY]
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={
                    CONF_COUNTRY: self._country,
                    CONF_STATE: self._state,
                    CONF_CITY: self._city,
                },
                options={
                    CONF_SENSORS: ALL_SENSORS,
                },
            )

        try:
            client = await self._ensure_client()
            cities = await client.get_cities(self._country, self._state)
        except Exception:
            errors["base"] = "cannot_fetch_cities"
            cities = []

        if not cities:
            cities_map = {
                ("IN", "DL"): [
                    {"slug": "delhi", "name": "New Delhi"},
                    {"slug": "noida", "name": "Noida"},
                    {"slug": "gurugram", "name": "Gurugram"},
                ],
                ("IN", "MH"): [
                    {"slug": "mumbai", "name": "Mumbai"},
                    {"slug": "pune", "name": "Pune"},
                    {"slug": "nagpur", "name": "Nagpur"},
                ],
            }
            cities = cities_map.get((self._country, self._state), [])

        return self.async_show_form(
            step_id="city",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CITY): _city_selector(cities),
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of the integration."""
        return await self.async_step_reconfigure_init()

    async def async_step_reconfigure_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration initialization."""
        self._set_confirm_only()
        return await self.async_step_reconfigure_country()

    async def async_step_reconfigure_country(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration country selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._country = user_input[CONF_COUNTRY]
            return await self.async_step_reconfigure_state()

        try:
            client = await self._ensure_client()
            countries = await client.get_countries()
        except Exception:
            errors["base"] = "cannot_fetch_countries"
            countries = []

        if not countries:
            countries = [
                {"code": "IN", "name": "India"},
                {"code": "US", "name": "United States"},
                {"code": "GB", "name": "United Kingdom"},
                {"code": "CA", "name": "Canada"},
                {"code": "AU", "name": "Australia"},
            ]

        return self.async_show_form(
            step_id="reconfigure_country",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COUNTRY): _country_selector(countries),
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure_state(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration state selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._state = user_input[CONF_STATE]
            return await self.async_step_reconfigure_city()

        try:
            client = await self._ensure_client()
            states = await client.get_states(self._country)
        except Exception:
            errors["base"] = "cannot_fetch_states"
            states = []

        if not states:
            states_map = {
                "IN": [
                    {"code": "DL", "name": "Delhi"},
                    {"code": "MH", "name": "Maharashtra"},
                    {"code": "KA", "name": "Karnataka"},
                    {"code": "TN", "name": "Tamil Nadu"},
                ],
                "US": [
                    {"code": "CA", "name": "California"},
                    {"code": "TX", "name": "Texas"},
                    {"code": "NY", "name": "New York"},
                    {"code": "FL", "name": "Florida"},
                ],
            }
            states = states_map.get(self._country, [])

        return self.async_show_form(
            step_id="reconfigure_state",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATE): _state_selector(states),
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure_city(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration city selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._city = user_input[CONF_CITY]
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(),
                data_updates={
                    CONF_COUNTRY: self._country,
                    CONF_STATE: self._state,
                    CONF_CITY: self._city,
                },
                options={
                    CONF_SENSORS: ALL_SENSORS,
                },
            )

        try:
            client = await self._ensure_client()
            cities = await client.get_cities(self._country, self._state)
        except Exception:
            errors["base"] = "cannot_fetch_cities"
            cities = []

        if not cities:
            cities_map = {
                ("IN", "DL"): [
                    {"slug": "delhi", "name": "New Delhi"},
                    {"slug": "noida", "name": "Noida"},
                    {"slug": "gurugram", "name": "Gurugram"},
                ],
                ("IN", "MH"): [
                    {"slug": "mumbai", "name": "Mumbai"},
                    {"slug": "pune", "name": "Pune"},
                    {"slug": "nagpur", "name": "Nagpur"},
                ],
            }
            cities = cities_map.get((self._country, self._state), [])

        return self.async_show_form(
            step_id="reconfigure_city",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CITY): _city_selector(cities),
                }
            ),
            errors=errors,
        )

