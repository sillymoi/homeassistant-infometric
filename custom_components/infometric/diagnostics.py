"""Diagnostics support for Infometric Panorama integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {CONF_PASSWORD, CONF_USERNAME}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN].get(entry.entry_id)

    data: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": entry.options,
        }
    }

    if coordinator:
        data["coordinator"] = {
            "last_update_success": getattr(coordinator, "last_update_success", None),
            "last_update_time": getattr(coordinator, "last_update_time", None).isoformat()
            if getattr(coordinator, "last_update_time", None)
            else None,
        }
        if getattr(coordinator, "data", None):
            meters = []
            for meter_type in ["energy", "hotwater", "coldwater"]:
                meter = getattr(coordinator.data, meter_type, None)
                if meter:
                    meters.append(
                        {
                            "type": meter_type,
                            "id": meter.id,
                            "total": meter.total,
                            "monthly_average": meter.monthly_average,
                            "monthly_prognosis": meter.monthly_prognosis,
                        }
                    )
            data["meters"] = meters

    return data
