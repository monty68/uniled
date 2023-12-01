[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

# UniLED - The Universal Light Controller

UniLED supports the following range of BLE LED controllers:

### LED Chord
  - **SP107E** - SPI RGB(W) Controller

### LED Hue
  - **SP110E** - SPI RGB(W) Controller

### BanlanX
  - **SP601E**/**SP602E**/**SP608E** - Multi Channel SPI RGB Controllers
  
  - **SP613E**/**SP614E** - PWM Controllers
  - **SP630E** - PWM/SPI RGB, RGBW, RGBCCT Controller
  - **SP631E**/**SP641E** - PWM Single Color Controllers
  - **SP632E**/**SP642E** - PWM CCT Controllers
  - **SP633E**/**SP643E** - PWM RGB Controllers
  - **SP634E**/**SP644E** - PWM RGBW Controllers
  - **SP635E**/**SP645E** - PWM RGBCCT Controllers
  - **SP636E**/**SP646E** - SPI Single Color Controllers
  - **SP637E**/**SP647E** - SPI CCT Controllers
  - **SP638E**/**SP648E** - SPI RGB Controllers
  - **SP639E**/**SP649E** - SPI RGBW Controllers
  - **SP63AE**/**SP64AE** - SPI RGBCCT Controllers

*Note, for those controllers that support custom effects, such as the SP630E, UniLED only supports selecting the custom effect,
you will have to use the android or IOS app to configure it.*

---


{% if not installed %}
## Installation

### HACS Automated Installation

You can install this component through [HACS](https://hacs.xyz/) to easily receive updates.

After installing HACS, visit the HACS _Integrations_ pane and add `https://github.com/monty68/uniled` as an `Integration` by following [these instructions](https://hacs.xyz/docs/faq/custom_repositories/). You'll then be able to install it through the _Integrations_ pane.

### Manual Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `uniled`.
4. Download _all_ the files from the `custom_components/uniled/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Settings" -> "Devices & Services" -> "Integrations" click "+" and search for "Universal Light Controller"

{% endif %}

## Adding Devices and Model Identification Issues

UniLED does it's best to identify the exact model through a number of different mechanisms, however
if you are having difficulty adding a device, especially where it fails to identify the model. Then,
first try using the applicable Android/IOS app and ensure the device name is set to match the devices
model then attempt adding the device into Home Assistant. If it still fails, enable debugging (see below) in Home Assistant, re-attempt adding the device, then open an issue attaching the debug log 
output to assist with further invetigation.

## Debugging

To debug the integration, add the following to your `configuration.yaml`

```yaml
logger:
  default: warning
  logs:
    custom_components.uniled: debug
```

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)


<!---->

***
[ha-logo]: https://raw.githubusercontent.com/monty68/uniled/main/docs/img/ha-logo-32x32.png
[uniled]: https://github.com/monty68/uniled
[user_profile]: https://github.com/monty68
[buymecoffee]: https://www.buymeacoffee.com/monty68
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Monty-blue.svg?style=for-the-badge
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/v/release/monty68/uniled?display_name=release&include_prereleases&style=for-the-badge
[releases]: https://github.com/monty68/uniled/releases
[commits-shield]: https://img.shields.io/github/last-commit/monty68/uniled?style=for-the-badge
[commits]: https://github.com/monty68/uniled/commits/main
[license]: https://github.com/monty68/uniled/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/monty68/uniled.svg?style=for-the-badge

