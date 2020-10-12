import asyncio
from datetime import datetime

from homeassistant.components.binary_sensor import BinarySensorEntity

from . import const, hub


async def async_setup_entry(hass, config_entry, async_add_devices):
    hub = hass.data[const.DOMAIN][config_entry.entry_id]

    new_devices = []
    # IR remote binary sensor
    ir_binary_sensor = StateDetectorBinarySensor(hub, const.DEVICE_CLASS_IRRemote_BINARY)
    new_devices.append(ir_binary_sensor)
    hub.add_platform(ir_binary_sensor)

    # motion binary sensor
    motion_binary_sensor = StateDetectorBinarySensor(hub, const.DEVICE_CLASS_MOTION_BINARY)
    new_devices.append(motion_binary_sensor)
    hub.add_platform(motion_binary_sensor)

    async_add_devices(new_devices)

class StateDetectorBinarySensor(BinarySensorEntity):
    def __init__(self, hub, device_class):
        """Initialize the sensor."""
        self._device_class = device_class
        self._state = None
        self._last_trigger = None
        self._hub = hub

    @property
    def should_poll(self):
        """Return True if entity has to be polled for state."""
        return True

    @property
    def should_poll_frequently(self):
        """Return True if entity has to be polled for state."""
        return True

    @property
    def name(self):
        """Return entity name."""
        return f"smartball-{self._hub.hub_id}-{self.device_class}"

    @property
    def is_on(self):
        """Return if entity is on."""
        if self.last_trigger is None:
            return False

        return (datetime.now() - self.last_trigger).seconds < const.BINARY_SENSOR_STABLE_TIME

    @property
    def device_class(self):
        """Return device class."""
        return self._device_class

    @property
    def available(self):
        """Return True if entity is available."""
        return True

    @property
    def last_trigger(self):
        return self._last_trigger

    def update_state(self, data):
        """Update entity."""
        self._last_trigger = datetime.now()

    def update(self):
        """Update entity."""
        return self.is_on