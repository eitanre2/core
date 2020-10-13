import asyncio
from logging import getLogger

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import const, hub, services

_LOGGER = getLogger(__name__)

# List of platforms to support. There should be a matching .py file for each,
# eg <cover.py> and <sensor.py>
# PLATFORMS = ["remote", "sensor", "binary_sensor"]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Hello World component."""
    _LOGGER.info("started")
    hass.data.setdefault(const.DOMAIN, {})

    services.register_global_services(hass)

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    h = hub.Hub(hass, entry, entry.data["name"], entry.data["host"], entry.data["port"])
    hass.data[const.DOMAIN][entry.entry_id] = h

    await h.start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    h = hass.data[const.DOMAIN][entry.entry_id]
    await h.stop()

    return True
