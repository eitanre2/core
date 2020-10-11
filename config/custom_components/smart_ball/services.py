import asyncio

from homeassistant.core import HomeAssistant

from . import hub
from .const import DOMAIN


def register_services(h: hub.Hub, hass: HomeAssistant):
    async def set_IR_default(data):
        print(hass)
        for entity in h.entities:
            print(entity)
            pass

    hass.services.async_register(DOMAIN, 'set_IR_default', set_IR_default)


