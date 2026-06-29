"""Sensor platform for aqi_in."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import IAQI_BREAKPOINTS, DEFAULT_NAME, DOMAIN
from .coordinator import AQIDataUpdateCoordinator

IAQI_SENSORS: dict[str, dict[str, Any]] = {
    "pm25": {
        "name": "PM 2.5",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.PM25,
        "state_class": SensorStateClass.MEASUREMENT,
        "iaqi_key": "pm25",
    },
    "pm10": {
        "name": "PM 10",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.PM10,
        "state_class": SensorStateClass.MEASUREMENT,
        "iaqi_key": "pm10",
    },
    "no2": {
        "name": "NO₂",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.NITROGEN_DIOXIDE,
        "state_class": SensorStateClass.MEASUREMENT,
        "iaqi_key": "no2",
    },
    "so2": {
        "name": "SO₂",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.SULPHUR_DIOXIDE,
        "state_class": SensorStateClass.MEASUREMENT,
        "iaqi_key": "so2",
    },
    "co": {
        "name": "CO",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.CO,
        "state_class": SensorStateClass.MEASUREMENT,
        "iaqi_key": "co",
    },
    "o3": {
        "name": "O₃",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.OZONE,
        "state_class": SensorStateClass.MEASUREMENT,
        "iaqi_key": "o3",
    },
    "aqi": {
        "name": "AQI",
        "unit": None,
        "device_class": SensorDeviceClass.AQI,
        "state_class": SensorStateClass.MEASUREMENT,
        "iaqi_key": "aqi",
    },
}

WEATHER_SENSORS: dict[str, dict[str, Any]] = {
    "temperature": {
        "name": "Temperature",
        "unit": "°C",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "weather_key": "temp_c",
    },
    "humidity": {
        "name": "Humidity",
        "unit": "%",
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "weather_key": "humidity",
    },
    "wind_speed": {
        "name": "Wind Speed",
        "unit": "km/h",
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "weather_key": "wind_kph",
    },
    "pressure": {
        "name": "Pressure",
        "unit": "hPa",
        "device_class": SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "weather_key": "pressure_mb",
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: AQIDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    for sensor_type, config in IAQI_SENSORS.items():
        entities.append(
            AQIPollutantSensor(
                coordinator,
                sensor_type,
                config["name"],
                config["unit"],
                config["device_class"],
                config["state_class"],
                config["iaqi_key"],
            )
        )

    for sensor_type, config in WEATHER_SENSORS.items():
        entities.append(
            AQIWeatherSensor(
                coordinator,
                sensor_type,
                config["name"],
                config["unit"],
                config["device_class"],
                config["state_class"],
                config["weather_key"],
            )
        )

    async_add_entities(entities)


class AQIPollutantSensor(CoordinatorEntity, SensorEntity):
    """Representation of an IAQI pollutant sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        sensor_type: str,
        name: str,
        unit_of_measurement: str | None,
        device_class: SensorDeviceClass,
        state_class: SensorStateClass,
        iaqi_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._iaqi_key = iaqi_key
        self._attr_name = f"{DEFAULT_NAME} {name}"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{sensor_type}"
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.slug)},
            "name": coordinator.config_entry.title,
            "manufacturer": "AQI.in",
            "model": "Air Quality Station",
        }

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        data_list = self.coordinator.data
        if not data_list:
            return None
        location = data_list[0]
        iaqi = getattr(location, "iaqi", None)
        if not isinstance(iaqi, dict):
            return None
        value = iaqi.get(self._iaqi_key)
        if value is None:
            return None
        return round(float(value), 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return None

        data_list = self.coordinator.data
        if not data_list:
            return None
        location = data_list[0]
        attrs: dict[str, Any] = {}

        if self._sensor_type != "aqi" and self._sensor_type in IAQI_BREAKPOINTS:
            iaqi = getattr(location, "iaqi", {})
            if isinstance(iaqi, dict) and self._iaqi_key in iaqi:
                try:
                    value = float(iaqi[self._iaqi_key])
                    aqi = self._calculate_aqi(value, self._sensor_type)
                    attrs["aqi"] = round(aqi)
                    attrs["aqi_category"] = self._get_aqi_category(aqi)
                except (ValueError, TypeError):
                    pass

        updated_at = getattr(location, "updated_at", None) or getattr(
            location, "updatedAt", None
        )
        if updated_at:
            attrs["last_updated"] = updated_at

        return attrs

    def _calculate_aqi(self, value: float, pollutant: str) -> float:
        """Calculate AQI based on pollutant concentration."""
        if pollutant not in IAQI_BREAKPOINTS:
            return 0.0

        breakpoints = IAQI_BREAKPOINTS[pollutant]

        for bp_low, bp_high, aqi_low, aqi_high in breakpoints:
            if bp_low <= value <= bp_high:
                return ((aqi_high - aqi_low) / (bp_high - bp_low)) * (
                    value - bp_low
                ) + aqi_low

        if breakpoints:
            return breakpoints[-1][3]

        return 0.0

    @staticmethod
    def _get_aqi_category(aqi: float) -> str:
        """Get AQI category description."""
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Satisfactory"
        elif aqi <= 200:
            return "Moderately polluted"
        elif aqi <= 300:
            return "Poor"
        elif aqi <= 400:
            return "Very poor"
        else:
            return "Severe"


class AQIWeatherSensor(CoordinatorEntity, SensorEntity):
    """Representation of a weather sensor from AQI.in location data."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        sensor_type: str,
        name: str,
        unit_of_measurement: str | None,
        device_class: SensorDeviceClass,
        state_class: SensorStateClass,
        weather_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._weather_key = weather_key
        self._attr_name = f"{DEFAULT_NAME} {name}"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{sensor_type}"
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.slug)},
            "name": coordinator.config_entry.title,
            "manufacturer": "AQI.in",
            "model": "Air Quality Station",
        }

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        data_list = self.coordinator.data
        if not data_list:
            return None
        location = data_list[0]
        weather = getattr(location, "weather", None)
        if not isinstance(weather, dict):
            return None
        value = weather.get(self._weather_key)
        if value is None:
            return None
        return round(float(value), 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return None
        data_list = self.coordinator.data
        if not data_list:
            return None
        location = data_list[0]
        attrs: dict[str, Any] = {}
        updated_at = getattr(location, "updated_at", None) or getattr(
            location, "updatedAt", None
        )
        if updated_at:
            attrs["last_updated"] = updated_at
        return attrs
