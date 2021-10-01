"""Infometric"""
from dataclasses import dataclass
import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
#    STATE_CLASS_TOTAL,
    STATE_CLASS_TOTAL_INCREASING,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_GAS,
    ENERGY_KILO_WATT_HOUR,
    VOLUME_CUBIC_METERS,
)
from homeassistant.core import DOMAIN, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_NAME, DOMAIN
from .infometric import InfometricClient, InfometricException

_LOGGER = logging.getLogger(__name__)

STATE_CLASS_TOTAL = "total"

DOMAIN_CONFIG = "config"

DAILY_SCAN_INTERVAL = timedelta(hours=1)
DAILY_NAME = "Infometric total"
PROGNOSIS_NAME = "Infometric monthly prognosis"
AVERAGE_NAME = "Infometric monthly average"

DAILY_TYPE = "day"
MONTHLY_TYPE = "month"
YEARLY_TYPE = "year"

GROUP_ENERGY = "energy"
GROUP_WATER = "water"

COUNTER_DAILY = "total"
COUNTER_AVERAGE = "monthly_average"
COUNTER_PROGNOSIS = "monthly_prognosis"

# CONFIG_SCHEMA = vol.Schema(
#     {DOMAIN: vol.Schema(CONFIG_SCHEMA_IN, extra=vol.ALLOW_EXTRA)}
# )
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_URL): cv.url,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

import async_timeout
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Config entry example."""
    # assuming API object stored here by __init__.py
    hass.data.setdefault(DOMAIN, {})
    config = entry.data
    coordinator = await get_coordinator(
        hass,
        entry.entry_id,
        config["url"],
        config["username"],
        config["password"],
    )

    #
    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    await coordinator.async_config_entry_first_refresh()

    sensors = []

    sensors.append(
        InfometricSensor(
            coordinator, DAILY_NAME, GROUP_ENERGY, DAILY_TYPE, COUNTER_DAILY
        )
    )
    sensors.append(
        InfometricSensor(
            coordinator,
            AVERAGE_NAME,
            GROUP_ENERGY,
            MONTHLY_TYPE,
            COUNTER_AVERAGE,
        )
    )
    sensors.append(
        InfometricSensor(
            coordinator,
            PROGNOSIS_NAME,
            GROUP_ENERGY,
            MONTHLY_TYPE,
            COUNTER_PROGNOSIS,
        )
    )
    sensors.append(
        InfometricSensor(
            coordinator, DAILY_NAME, GROUP_WATER, DAILY_TYPE, COUNTER_DAILY
        )
    )
    sensors.append(
        InfometricSensor(
            coordinator,
            AVERAGE_NAME,
            GROUP_WATER,
            MONTHLY_TYPE,
            COUNTER_AVERAGE,
        )
    )
    sensors.append(
        InfometricSensor(
            coordinator,
            PROGNOSIS_NAME,
            GROUP_WATER,
            MONTHLY_TYPE,
            COUNTER_PROGNOSIS,
        )
    )

    async_add_entities(sensors)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Infometric component."""
    _LOGGER.debug("async_setup, config: %s", config)
    # conf_default = CONFIG_SCHEMA({DOMAIN: {}})[DOMAIN]
    # conf = config.get(DOMAIN, conf_default)
    # hass.data[DOMAIN] = {
    #     DOMAIN_CONFIG: conf,
    # }

    # Only start if set up via configuration.yaml.
    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
            )
        )

    return True


async def get_coordinator(
    hass: HomeAssistant, id: str, url: str, username: str, password: str
) -> DataUpdateCoordinator:
    """Get the data update coordinator."""

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(60):
                client = InfometricClient(
                    url,
                    username,
                    password,
                )
                await client.authenticate(async_get_clientsession(hass))
                meters = await client.get_meters()
                return InfometricData.from_meters(meters)

        except InfometricException as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=DAILY_SCAN_INTERVAL,
    )
    # await hass.data[DOMAIN].async_refresh()
    # await coordinator.async_config_entry_first_refresh()
    return coordinator


@dataclass
class DataEntry:
    """Stores a single meter group"""

    id: str
    total: float
    monthly_prognosis: float
    monthly_average: float


@dataclass
class InfometricData:
    """Stores data retrieved from Panorama."""

    energy: DataEntry
    water: DataEntry

    @staticmethod
    def from_meters(meters):
        energy = None
        water = None

        for m in meters:
            _LOGGER.debug(f"Updating Infometric meters. Got: {m}")

            id = f"{m.id}-{m.name}"
            prognosis = m.prognosis
            average = m.average
            daily = float(m.last_values[0]["value"])
            if not len(m.last_values) == 1:
                _LOGGER.warning(f"Infometric sensor with multiple series: {m}")

            entry = DataEntry(id, daily, prognosis, average)
            if m.name.startswith("El"):
                energy = entry
            elif m.name.startswith("Varmvatten"):
                water = entry
            else:
                _LOGGER.warning(f"Infometric sensor with unknown name: {m}")
                energy = entry
        return InfometricData(energy=energy, water=water)


class InfometricSensor(CoordinatorEntity, SensorEntity):
    """Representation of a sensor entity for Infometric."""

    def __init__(self, coordinator, name, group, sensor_type, counter):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

        """Initialize the sensor."""
        self._group = group
        self._sensor_type = sensor_type
        self._counter = counter

        entry = getattr(self.coordinator.data, self._group)
        prefix = getattr(entry, "id")
        self._attr_unique_id = f"{prefix}_{self._group}_{self._counter}"
        self._attr_name = f"{name} {self._group}"

        if group == GROUP_ENERGY:
            self._attr_device_class = DEVICE_CLASS_ENERGY
            self._attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR
        else:
            self._attr_device_class = DEVICE_CLASS_GAS
            self._attr_native_unit_of_measurement = VOLUME_CUBIC_METERS

        if sensor_type == DAILY_TYPE:
            self._attr_state_class = STATE_CLASS_TOTAL_INCREASING
        else:
            self._attr_state_class = STATE_CLASS_TOTAL

    @property
    def native_value(self) -> StateType:
        """Update device state."""
        entry = getattr(self.coordinator.data, self._group)
        return getattr(entry, self._counter)
