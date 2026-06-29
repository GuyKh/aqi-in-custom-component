# Air Quality India (AQI.in) Integration for Home Assistant

<p align="center">
  <img src="custom_components/aqi_in/www/logo.png" alt="AQI.in Logo" width="200">
</p>

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]
[![Maintenance][maintenance-shield]][maintainer]

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
   - Repository: `https://github.com/GuyKh/aqi-in-custom-component`
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
- Timestamp of last update
- Station name

## Data Source

This integration uses the [AQI.in API](https://aqicn.org/api/) to provide air quality data. The data is updated every 10 minutes by default.

## Configuration Options

In the configuration flow, you can select:
- Country (defaults to India)
- State/Province
- City
- Sensors to monitor (you can select multiple)

## Node-RED Integration

The entities created by this integration can be used in Node-RED just like any other Home Assistant entities.

## Troubleshooting

If you experience issues with the integration:
1. Check your Home Assistant logs for errors related to `aqi_in`
2. Verify your internet connection
3. Make sure the AQI.in service is available in your region
4. Try reloading the integration from the UI
5. If problems persist, please open an issue on GitHub

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions and support, please open an issue on the GitHub repository.

## Thanks for reading 😄
If you have found this useful, please consider buying me a coffee to support more content like this! [![Buy me a coffee][buymecoffeebadge]][buymecoffee]

[releases-shield]: https://img.shields.io/github/release/guykh/aqi-in-custom-component.svg?style=for-the-badge
[releases]: https://github.com/guykh/aqi-in-custom-component/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/guykh/aqi-in-custom-component.svg?style=for-the-badge
[commits]: https://github.com/guykh/aqi-in-custom-component/commits/main
[license-shield]: https://img.shields.io/github/license/guykh/aqi-in-custom-component.svg?style=for-the-badge
[license]: LICENSE
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[buymecoffee]: https://www.buymeacoffee.com/guykh
[maintenance-shield]: https://img.shields.io/badge/maintainer-Guy%20Khmelnitsky%20%40GuyKh-blue.svg?style=for-the-badge
[maintainer]: https://github.com/guykh
