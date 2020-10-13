import asyncio

from homeassistant.components.remote import RemoteEntity
from homeassistant.helpers.entity import Entity

from . import const, hub


async def async_setup_entry(hass, config_entry, async_add_devices):
    hub = hass.data[const.DOMAIN][config_entry.entry_id]

    new_devices = []
    for command in hub.remote_commands:
        r = IRRemote(hub, command)
        hub.add_platform(r)
        new_devices.append(r)

    if len(new_devices) > 0:
        async_add_devices(new_devices)

class IRRemote(RemoteEntity):
    def __init__(self, hub: hub.Hub, command):
        """Initialize the Demo Remote."""
        self._name = f"smartball-{hub.hub_id_short}-remote-{command}"
        self._icon = "mdi:remote"
        self._hub = hub
        self.command = command

    @property
    def device_class(self):
        """Return the device_class of the sensor."""
        return const.DEVICE_CLASS_IRRemote

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def is_on(self):
        return False

    def turn_on(self, **kwargs):
        asyncio.run(self.send_command([self.command]))
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        self._state = False
        self.schedule_update_ha_state()

    async def send_command(self, commands, **kwargs):
        for com in commands:
            await self._hub.remote_command(com)