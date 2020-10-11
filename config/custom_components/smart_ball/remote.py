from homeassistant.components.remote import RemoteEntity
from homeassistant.helpers.entity import Entity

from . import hub
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_devices):
    hub = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for command in hub.remote_commands:
        new_devices.append(IRRemote(hub, command))
    if new_devices:
        async_add_devices(new_devices)

class IRRemote(RemoteEntity):
    def __init__(self, hub: hub.Hub, command):
        """Initialize the Demo Remote."""
        self._name = f"IR Remote Control - {command}"
        self._icon = "mdi:remote"
        self._hub = hub
        self._hub.add_platform(self)
        self.command = command
        self._last_command_sent = None

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

    @property
    def device_state_attributes(self):
        if self._last_command_sent is not None:
            return {"last_command_sent": self._last_command_sent}

    def turn_on(self, **kwargs):
        # self._state = True
        # self.schedule_update_ha_state()
        self.send_command([self.command])

    def turn_off(self, **kwargs):
        self._state = False
        self.schedule_update_ha_state()

    def send_command(self, commands, **kwargs):
        for com in commands:
            self._last_command_sent = com
            self._hub.send_command('scenes/IR_scene/command', {"name":"play", "code": com})
        self.schedule_update_ha_state()