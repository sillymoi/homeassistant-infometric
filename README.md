# Home Assistant Infometric Integration

This custom integration is used to import data from Infometric Panorama Home to Home Assistant.

## Description

This custom integration is used to import data from Infometric Panorama Home to Home Assistant. It support 3 type of meters
* Energy meter
* Hot water meter
* Cold water meter

For each meter it will create 3 entites
* Total
* Monthly average
* Monthly prognosis

## Getting Started

### Dependencies

* Smart meters installed in your appartment connected to Infometric
* Account to access Panorama Home

### Limitations
You can only have one meter of each type.

### Installing

Choose one of the two installation options below

#### Automatic installation (preferred)
Install using HACS:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=homeassistant-infometric&owner=sillymoi)


#### Manual installation
* Copy all files to homeassistant/custom_components/infometric
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
    * Support of HACS installation
    * Removal of hardcoded meters
* 0.0.1
    * Initial Release


## Acknowledgments

* [README-Template](https://gist.github.com/DomPizzie/7a5ff55ffa9081f2de27c315f5018afc)
