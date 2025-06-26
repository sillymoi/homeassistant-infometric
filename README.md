# Home Assistant Infometric Integration

This custom integration is used to import data from Infometric Panorama Home to Home Assistant.

## Description

This custom integration is used to import data from Infometric Panorama Home to Home Assistant. It will create 9 entities:
* Total energy
* Monthly average energy
* Montly prognosis energy
* Total hot water
* Monthly average hot water
* Montly prognosis hot water
* Total cold water
* Monthly average cold water
* Montly prognosis cold water

## Getting Started

### Dependencies

* Smart meters installed in your appartment connected to Infometric
* Account to access Panorama Home

### Limitations

* Right now hardcoded for 3 meters
    * Energy meter
    * Hot water
    * Cold water

### Installing

* Copy all files to homeassistant/custom_components/homeassistant-infometric
* Restart Home Assistant

### Initial setup

Add the integration as any other integration: Settings > Devices & services > Add integration

You will be requested for 3 things:
* URL to the Panorama home (usually https://lgh.infometric.se/)
* Username (usually your email)
* Password to Panorama Home

The name field is if you want to rename the integration something other than Infometric.

## Authors

* The main development of this integration is made by @sillymoi in 2021 (https://github.com/sillymoi/homeassistant-infometric)
* Small updates were done by @AndersMarkoff in 2025 (https://github.com/AndersMarkoff/homeassistant-infometric)


## Version History

* 0.0.2
    * Small adaptations to the Infometric API
    * Uplift to home assistant 2025.5.3
    * Support for hot and cold water
* 0.0.1
    * Initial Release


## Acknowledgments

* [README-Template](https://gist.github.com/DomPizzie/7a5ff55ffa9081f2de27c315f5018afc)
* [Original Infometric integration by @sillymoi](https://github.com/sillymoi/homeassistant-infometric)