import asyncio
from datetime import datetime

from homeassistant.helpers.entity import Entity

from . import const, hub

FREQUENT_SENSORS = [const.DEVICE_CLASS_MOTION, const.DEVICE_CLASS_UPTIME]


async def async_setup_entry(hass, config_entry, async_add_devices):
    hub = hass.data[const.DOMAIN][config_entry.entry_id]

    new_devices = []
    # temp sensor
    temp_sensor = GenericSensor(hub, const.DEVICE_CLASS_TEMPERATURE)
    new_devices.append(temp_sensor)
    hub.add_platform(temp_sensor)

    # humidity sensor
    hum_sensor = GenericSensor(hub, const.DEVICE_CLASS_HUMIDITY)
    new_devices.append(hum_sensor)
    hub.add_platform(hum_sensor)

    # signal_strength sensor (ldr)
    ldr_sensor = GenericSensor(hub, const.DEVICE_CLASS_LDR)
    new_devices.append(ldr_sensor)
    hub.add_platform(ldr_sensor)

    # motion sensor
    motion_sensor = GenericSensor(hub, const.DEVICE_CLASS_MOTION)
    new_devices.append(motion_sensor)
    hub.add_platform(motion_sensor)

    # uptime sensor
    uptime_sensor = GenericSensor(hub, const.DEVICE_CLASS_UPTIME)
    new_devices.append(uptime_sensor)
    hub.add_platform(uptime_sensor)

    async_add_devices(new_devices)

class GenericSensor(Entity):
    def __init__(self, hub, device_class):
        """Initialize the sensor."""
        self._device_class = device_class
        self._state = None
        self._last_update = None
        self._hub = hub

    @property
    def name(self):
        return f"smartball-{self._hub.hub_id_short}-{self.device_class}"

    @property
    def device_class(self):
        """Return the device_class of the sensor."""
        return self._device_class
    
    @property
    def should_poll_frequently(self):
        """Return True if entity has to be polled for state."""
        return self.device_class in FREQUENT_SENSORS

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the unit of measurement."""
        if self._device_class == const.DEVICE_CLASS_TEMPERATURE:
            return 'hass:thermometer'
        if self._device_class == const.DEVICE_CLASS_HUMIDITY:
            return 'hass:percent'
        if self._device_class == const.DEVICE_CLASS_LDR:
            return 'mdi:weather-sunny'
        if self._device_class == const.DEVICE_CLASS_MOTION:
            return 'mdi:timer-outline'
        if self._device_class == const.DEVICE_CLASS_UPTIME:
            return 'mdi:timer-outline'

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._device_class == const.DEVICE_CLASS_TEMPERATURE:
            return const.TEMP_CELSIUS
        if self._device_class == const.DEVICE_CLASS_HUMIDITY:
            return '%'
        if self._device_class == const.DEVICE_CLASS_LDR:
            return '%'
        if self._device_class == const.DEVICE_CLASS_MOTION:
            return 'seconds'
        if self._device_class == const.DEVICE_CLASS_UPTIME:
            return 'seconds'

    def update_state(self, data):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = int(data['value'])
        self._last_update = datetime.now()

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        if (self._last_update is not None) and (self._state is not None) and (self._device_class in(const.DEVICE_CLASS_MOTION)):
            new_state = self._state - (datetime.now() - self._last_update).seconds
            self._state = max(new_state, 0)