import asyncio
from logging import getLogger

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import hub, services
from .const import DOMAIN

_LOGGER = getLogger(__name__)

# List of platforms to support. There should be a matching .py file for each,
# eg <cover.py> and <sensor.py>
PLATFORMS = ["remote"] #["sensor"]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Hello World component."""
    _LOGGER.info("started")
    hass.data.setdefault(DOMAIN, {})

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    h = hub.Hub(hass, entry.data["host"], entry.data["port"])
    hass.data[DOMAIN][entry.entry_id] = h

    await h.connect()

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    # register services
    services.register_services(h, hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    h = hass.data[DOMAIN][entry.entry_id]
    h.stop()
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
