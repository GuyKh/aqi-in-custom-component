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

from .const import (
    IAQI_BREAKPOINTS,
    DEFAULT_NAME,
    DOMAIN,
)
from .coordinator import AQIDataUpdateCoordinator

# Mapping of sensor types to their units and device classes
SENSOR_TYPES_DETAILS = {
    "pm25": {
        "name": "PM 2.5",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.PM25,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "pm10": {
        "name": "PM 10",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.PM10,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "no2": {
        "name": "NO₂",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.NITROGEN_DIOXIDE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "so2": {
        "name": "SO₂",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.SULPHUR_DIOXIDE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "co": {
        "name": "CO",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.CARBON_MONOXIDE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "o3": {
        "name": "O₃",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.OZONE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "nh3": {
        "name": "NH₃",
        "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "device_class": SensorDeviceClass.AMMONIA,
        "state_class": SensorStateClass.MEASUREMENT,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: AQIDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for sensor_type in coordinator.selected_sensors:
        if sensor_type in SENSOR_TYPES_DETAILS:
            entities.append(
                AQISensor(
                    coordinator,
                    sensor_type,
                    SENSOR_TYPES_DETAILS[sensor_type]["name"],
                    SENSOR_TYPES_DETAILS[sensor_type]["unit"],
                    SENSOR_TYPES_DETAILS[sensor_type]["device_class"],
                    SENSOR_TYPES_DETAILS[sensor_type]["state_class"],
                )
            )

    async_add_entities(entities)


class AQISensor(CoordinatorEntity, SensorEntity):
    """Representation of an AQI sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        sensor_type: str,
        name: str,
        unit_of_measurement: str,
        device_class: SensorDeviceClass,
        state_class: SensorStateClass,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"{DEFAULT_NAME} {name}"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{sensor_type}"
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_device_class = device_class
        self._attr_state_class = state_class

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
            
        # Get the raw value from the data
        value = self.coordinator.data.get(self._sensor_type)
        if value is None:
            return None
            
        return round(float(value), 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return None

        attrs: dict[str, Any] = {}
        
        # Add AQI information if available
        if self._sensor_type in IAQI_BREAKPOINTS and self.coordinator.data.get(self._sensor_type) is not None:
            try:
                value = float(self.coordinator.data.get(self._sensor_type, 0))
                aqi = self._calculate_aqi(value, self._sensor_type)
                attrs["aqi"] = round(aqi)
                attrs["aqi_category"] = self._get_aqi_category(aqi)
            except (ValueError, TypeError):
                pass
        
        # Add timestamp if available
        if "last_updated" in self.coordinator.data:
            attrs["last_updated"] = self.coordinator.data["last_updated"]
            
        return attrs

    def _calculate_aqi(self, value: float, pollutant: str) -> float:
        """Calculate AQI based on pollutant concentration."""
        if pollutant not in IAQI_BREAKPOINTS:
            return 0.0
            
        breakpoints = IAQI_BREAKPOINTS[pollutant]
        
        # Find the appropriate breakpoint range
        for bp_low, bp_high, aqi_low, aqi_high in breakpoints:
            if bp_low <= value <= bp_high:
                # Linear interpolation
                return ((aqi_high - aqi_low) / (bp_high - bp_low)) * (value - bp_low) + aqi_low
        
        # If value is above the highest breakpoint, return the maximum AQI
        if breakpoints:
            return breakpoints[-1][3]  # Return the highest AQI value
        
        return 0.0

    def _get_aqi_category(self, aqi: float) -> str:
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