"""Config flow for aqi_in integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

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

# Steps:
# 1. Select country
# 2. Select state
# 3. Select city
# 4. Select sensors

class AQIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for aqi_in."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._aqi_client: AQIClient | None = None
        self._country: str | None = None
        self._state: str | None = None
        self._city: str | None = None

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
            if self._aqi_client is None:
                self._aqi_client = AQIClient()
            
            countries = await self._aqi_client.get_countries()
        except Exception:
            errors["base"] = "cannot_fetch_countries"
            countries = []

        if not countries:
            # Fallback to common countries if API fails
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
                    vol.Required(CONF_COUNTRY): vol.In(
                        {country["code"]: country["name"] for country in countries}
                    )
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
            if self._aqi_client is None:
                self._aqi_client = AQIClient()
            
            states = await self._aqi_client.get_states(self._country)
        except Exception:
            errors["base"] = "cannot_fetch_states"
            states = []

        if not states:
            # Fallback for common countries
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
                    vol.Required(CONF_STATE): vol.In(
                        {state["code"]: state["name"] for state in states}
                    )
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
            return await self.async_step_sensors()

        try:
            if self._aqi_client is None:
                self._aqi_client = AQIClient()
            
            cities = await self._aqi_client.get_cities(self._country, self._state)
        except Exception:
            errors["base"] = "cannot_fetch_cities"
            cities = []

        if not cities:
            # Fallback for common cities
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
                    vol.Required(CONF_CITY): vol.In(
                        {city["slug"]: city["name"] for city in cities}
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the sensor selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={
                    CONF_COUNTRY: self._country,
                    CONF_STATE: self._state,
                    CONF_CITY: self._city,
                },
                options={
                    CONF_SENSORS: user_input[CONF_SENSORS],
                },
            )

        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SENSORS, default=list(SENSOR_TYPES.keys())
                    ): cv.multi_select(SENSOR_TYPES)
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
            if self._aqi_client is None:
                self._aqi_client = AQIClient()
            
            countries = await self._aqi_client.get_countries()
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
                    vol.Required(CONF_COUNTRY): vol.In(
                        {country["code"]: country["name"] for country in countries}
                    )
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
            if self._aqi_client is None:
                self._aqi_client = AQIClient()
            
            states = await self._aqi_client.get_states(self._country)
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
                    vol.Required(CONF_STATE): vol.In(
                        {state["code"]: state["name"] for state in states}
                    )
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
            return await self.async_step_reconfigure_sensors()

        try:
            if self._aqi_client is None:
                self._aqi_client = AQIClient()
            
            cities = await self._aqi_client.get_cities(self._country, self._state)
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
                    vol.Required(CONF_CITY): vol.In(
                        {city["slug"]: city["name"] for city in cities}
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration sensor selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(),
                data_updates={
                    CONF_COUNTRY: self._country,
                    CONF_STATE: self._state,
                    CONF_CITY: self._city,
                },
                options={
                    CONF_SENSORS: user_input[CONF_SENSORS],
                },
            )

        return self.async_show_form(
            step_id="reconfigure_sensors",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SENSORS, 
                        default=self._get_reconfigure_entry().options.get(
                            CONF_SENSORS, list(SENSOR_TYPES.keys())
                        )
                    ): cv.multi_select(SENSOR_TYPES)
                }
            ),
            errors=errors,
        )