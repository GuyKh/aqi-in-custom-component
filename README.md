# Air Quality India (AQI.in) Integration for Home Assistant

This custom component provides access to air quality data from [AQI.in](https://aqicn.org/) for Home Assistant.

## Features

- Real-time air quality data from monitoring stations across India
- Multiple pollutant sensors (PM2.5, PM10, NO2, SO2, CO, O3, NH3)
- Indian Air Quality Index (IAQI) calculation
- Configurable via UI with country/state/city selection
- Support for multiple sensors per location

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS:
   - Repository: `https://github.com/air-sviva/aqi-in-custom-component`
   - Category: Integration

2. Search for "Air Quality India" in HACS and install it
3. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/aqi_in` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

The integration can be configured via the Home Assistant UI:

1. Go to Settings > Devices & Services
2. Click "+ Add Integration"
3. Search for "Air Quality India" and select it
4. Follow the setup wizard to select your country, state, city, and sensors

## Sensors

The following sensors are available:

- PM2.5 (Particulate Matter ≤ 2.5µm)
- PM10 (Particulate Matter ≤ 10µm)
- NO₂ (Nitrogen Dioxide)
- SO₂ (Sulfur Dioxide)
- CO (Carbon Monoxide)
- O₃ (Ozone)
- NH₃ (Ammonia)

Each sensor provides:
- Current concentration value
- Indian Air Quality Index (IAQI) in attributes
- IAQI category (Good, Satisfactory, Moderately polluted, Poor, Very poor, Severe)

## Data Source

This integration uses the [AQI.in API](https://aqicn.org/api/) to provide air quality data. The data is updated every 10 minutes by default.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Based on the [air-sviva-custom-component](https://github.com/air-sviva/air-sviva-custom-component) template
- Uses the [aqi-in-api](https://pypi.org/project/aqi-in-api/) Python package