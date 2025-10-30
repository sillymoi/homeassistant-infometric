"""Infometric sensors and coordinator."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
    SensorStateClass,
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
    UnitOfEnergy,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
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

DOMAIN_CONFIG = "config"

DAILY_SCAN_INTERVAL = timedelta(hours=1)
DAILY_NAME = "Infometric total"
PROGNOSIS_NAME = "Infometric monthly prognosis"
AVERAGE_NAME = "Infometric monthly average"

DAILY_TYPE = "day"
MONTHLY_TYPE = "month"
YEARLY_TYPE = "year"

GROUP_ENERGY = "energy"
GROUP_HOTWATER = "hotwater"
GROUP_COLDWATER = "coldwater"

COUNTER_DAILY = "total"
COUNTER_AVERAGE = "monthly_average"
COUNTER_PROGNOSIS = "monthly_prognosis"

# CONFIG_SCHEMA = vol.Schema(
#     {DOMAIN: vol.Schema(CONFIG_SCHEMA_IN, extra=vol.ALLOW_EXTRA)}
# )
PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_URL, default="https://lgh.infometric.se/"): cv.url,
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

    for group in [GROUP_ENERGY, GROUP_HOTWATER, GROUP_COLDWATER]:
        data = getattr(coordinator.data, group)
        if data != None:
            sensors.append(
                InfometricSensor(
                    coordinator, DAILY_NAME, group, DAILY_TYPE, COUNTER_DAILY
                )
            )
            sensors.append(
                InfometricSensor(
                    coordinator, AVERAGE_NAME, group, MONTHLY_TYPE, COUNTER_AVERAGE
                )
            )
            sensors.append(
                InfometricSensor(
                    coordinator, PROGNOSIS_NAME, group, MONTHLY_TYPE, COUNTER_PROGNOSIS
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
                # Reuse existing client if available for session persistence
                store = hass.data[DOMAIN].setdefault("client_store", {})
                client: InfometricClient | None = store.get(id)
                if client is None:
                    client = InfometricClient(url, username, password)
                    store[id] = client
                    await client.authenticate(async_get_clientsession(hass))
                elif not client._authenticated:
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
    """Stores data retrieved from Panorama.

    Some meter types may be absent; fields can be None.
    """

    energy: DataEntry | None
    hotwater: DataEntry | None
    coldwater: DataEntry | None

    @staticmethod
    def from_meters(meters):
        energy: DataEntry | None = None
        hotwater: DataEntry | None = None
        coldwater: DataEntry | None = None

        for m in meters:
            _LOGGER.debug("Updating Infometric meters. Got meter id=%s name=%s", m.id, m.name)

            # Unique ID derived from UnitId only for stability
            unique_id = str(m.id)

            prognosis = float(m.prognosis)
            average = float(m.average)
            # Pick first value if available, else 0.0
            daily = 0.0
            if m.last_values:
                try:
                    daily_raw = m.last_values[0].get("value")
                    daily = float(daily_raw) if daily_raw not in (None, "") else 0.0
                except (ValueError, TypeError):
                    _LOGGER.warning("Invalid daily value for meter %s", m.id)
            if len(m.last_values) > 1:
                _LOGGER.debug("Meter %s has multiple series values; using first.", m.id)

            entry = DataEntry(unique_id, daily, prognosis, average)
            if m.name.startswith("El"):
                energy = entry
            elif m.name.startswith("Varmvatten"):
                hotwater = entry
            elif m.name.startswith("Kallvatten"):
                coldwater = entry
            else:
                _LOGGER.warning("Infometric sensor with unknown name pattern: %s", m.name)
        return InfometricData(energy=energy, hotwater=hotwater, coldwater=coldwater)


class InfometricSensor(CoordinatorEntity, SensorEntity):
    """Representation of a sensor entity for Infometric."""

    def __init__(self, coordinator, name: str, group: str, sensor_type: str, counter: str):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

        """Initialize the sensor."""
        self._group = group
        self._sensor_type = sensor_type
        self._counter = counter

        entry = getattr(self.coordinator.data, self._group, None)
        prefix = getattr(entry, "id", f"{group}_unknown")
        self._attr_unique_id = f"{prefix}_{self._group}_{self._counter}"
        self._attr_name = f"{name} {self._group}"
        self._attr_suggested_display_precision = 2

        # Set device class and state class based on sensor type
        if sensor_type == DAILY_TYPE:
            # Daily cumulative total - use device class + total state
            if group == GROUP_ENERGY:
                self._attr_device_class = SensorDeviceClass.ENERGY
                self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
            else:
                self._attr_device_class = SensorDeviceClass.WATER
                self._attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
            self._attr_state_class = SensorStateClass.TOTAL
        else:
            # Monthly average / prognosis - don't use device class (conflicts with measurement state)
            # Just set units without device class
            if group == GROUP_ENERGY:
                self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
            else:
                self._attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType:
        """Update device state."""
        data = getattr(self.coordinator, "data", None)
        if data is None:
            return None
        entry = getattr(data, self._group, None)
        if entry is None:
            return None
        return getattr(entry, self._counter, None)

    @property
    def device_info(self):  # type: ignore[override]
        """Return device information for grouping sensors."""
        # Use energy meter id if available as base; fallback to domain
        base_id = None
        data = getattr(self.coordinator, "data", None)
        if data and getattr(data, "energy", None):
            base_id = getattr(data.energy, "id", None)
        if not base_id:
            base_id = "infometric"
        return {
            "identifiers": {(DOMAIN, base_id)},
            "manufacturer": "Infometric AB",
            "name": "Infometric Panorama",
        }
