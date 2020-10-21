import asyncio
import hashlib
import json
from logging import getLogger
import queue
import threading
from threading import Timer
import time

import paho.mqtt.client as paho

from . import const, services

_LOGGER = getLogger(__name__)

HUBS = {}
PLATFORMS = ["remote", "sensor", "binary_sensor"]
COMMON_DEVICES = [  const.DEVICE_CLASS_TEMPERATURE, 
                    const.DEVICE_CLASS_HUMIDITY, 
                    const.DEVICE_CLASS_LDR, 
                    const.DEVICE_CLASS_MOTION, 
                    const.DEVICE_CLASS_UPTIME,
                    const.DEVICE_CLASS_MOTION_BINARY]
class Hub:
    def __init__(self, hass, entry, name, host, port):
        self._host = host
        self._port = port or 1883
        self._hass = hass
        self._entry = entry
        self._name = name
        self._hub_id = None
        self._has_config = False
        self.remote_commands = []
        self.entities = []
        self._client = None
        self._running = False
        # when true - just create connection. no entities should be created
        self._is_tester = False

    def add_platform(self, entity):
        self.entities.append(entity)

    @property
    def name(self):
        return self._name

    @property
    def is_tester(self):
        return self._is_tester

    @property
    def running(self):
        return self._running

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def remote_address(self):
        return f"{self.host}:{self.port}"

    @property
    def hub_id(self):
        return self._hub_id

    @property
    def hub_id_short(self):
        return self._hub_id[0:8]

    async def test_connection(self):
        self._is_tester = True
        await self.start()
        return self._has_config

    async def start(self):
        if self.running:
            return True

        self._running = True

        # messages queue
        self.pending_tasks_queue = queue.Queue()
        self.queue_thread = threading.Thread(target = self._queue_routine)
        self.queue_thread.start()

        # keepalive timer
        self._timer = Timer(0, self.timer_callback)
        self._timer.start()

        limit = 10
        _LOGGER.info("Smart-Ball at {slef.remote_address} is waiting for device config..")
        while not self._has_config and limit > 0:
            await asyncio.sleep(1)
            limit = limit - 1

        return True

    async def stop(self):
        self._running = False
        self._client_cleanup()
        await self._async_platforms_cleanup()

    async def remote_command(self, command_name):
        self.send_command('command/RemoteIR', {"command":"play", "code": command_name})

    async def remote_start_record(self, command_name):
        self.send_command('command/RemoteIR', {"command":"record", "code": command_name})

    def _client_cleanup(self):
        if self._client is not None:
            try:
                self._client.loop_stop()
            except Exception as ex:
                pass

            try:
                self._client.disconnect()
            except Exception as ex:
                pass

            self._client = None

    async def _async_platforms_cleanup(self):
        if not self._has_config:
            return
        self.entities = []
        for component in PLATFORMS:
            await self._hass.config_entries.async_forward_entry_unload(self._entry, component)

    def _queue_routine(self):
        while self.running:
            message = self.pending_tasks_queue.get()
            if message is None or message.topic is None:
                time.sleep(1)
            else:
                try:
                    self._handle_message(message)
                except Exception as message:
                    pass
                self.pending_tasks_queue.task_done()

    def _connect(self):
        self._client_cleanup()
        try:
            self._client = paho.Client()
            self._client.on_message = self._on_message
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.connect(self.host, port = int(self.port))
            self._client.loop_start()
        except Exception as ex:
            self._client_cleanup()
            _LOGGER.exception("Failed to connect to Smart-Ball at {self.remote_address}")

    def timer_callback(self):
        if not self.running:
            return
        if self._client is None:
            self._connect()
        else:
            for entity in self.entities:
                if hasattr(entity, 'should_poll_frequently') and entity.should_poll_frequently:
                    entity.schedule_update_ha_state(True)

        self._timer = Timer(const.REFRESH_INTERVAL, self.timer_callback)
        self._timer.start()

    def _on_connect(self, client, userdata, flags, rc):
        _LOGGER.info("Smart-Ball at {self.remote_address} connected")
        self._client.subscribe([("config/#", 0)])
        self._client.subscribe([("state/#", 0)])
 
    def _on_disconnect(self, client, userdata, rc):
        _LOGGER.exception("Smart-Ball at {self.remote_address} disconnected")   

    def _on_message(self, client, userdata, message):
        try:
            self._handle_message(message)
        except Exception as msg:
            _LOGGER.exception("Smart-Ball at {self.remote_address} failed to parse message from device:" + msg)

    def _handle_message(self, message):
        _LOGGER.info(f"Smart-Ball at {self.remote_address}. New MQTT message. topic={message.topic}")

        if message.topic.startswith('state'):
            message_json = json.loads(message.payload)
            for device in message_json['drivers']:
                try:
                    self._handle_topic_state(device['name'], device['data'])
                except Exception as msg:
                 _LOGGER.exception(f"Failed to update device ({device['name']}) value :" + msg)

        # HB from ball - it's alive!
        entity = self._find_entity(const.DEVICE_CLASS_ACTIVE)
        if entity is not None:
            entity.update_state({})
            entity.schedule_update_ha_state()

        if message.topic == 'config':
            self._handle_topic_config(json.loads(message.payload))

    def _handle_topic_state(self, driver_name, payload):
        if driver_name in COMMON_DEVICES:
            entity = self._find_entity(driver_name)
            if entity is None:
                return
            entity.update_state(payload)
            entity.schedule_update_ha_state()


    def _find_entity(self, device_class):
        for entity in self.entities:
            if entity.device_class == device_class:
                return entity
        return None

    def _handle_topic_config(self, payload):
        for driver in payload["drivers"]:
            if driver == "RemoteIR":
                self.remote_commands = payload["drivers"]['RemoteIR']['commands'] or []
        self._hub_id = payload["hub_id"]
        if self._is_tester:
            self._has_config = True
            return

        # register services
        services.register_services(self, self._hass)
        
        HUBS[self.hub_id] = self
        asyncio.run(self._async_platforms_cleanup())

        # This creates each HA object for each platform your device requires.
        # It's done by calling the `async_setup_entry` function in each platform module.
        for component in PLATFORMS:
            self._hass.async_create_task(
                self._hass.config_entries.async_forward_entry_setup(self._entry, component)
            )
        self._has_config = True
    
    def send_command(self, topic, message):
        self._client.publish(f"{topic}", json.dumps(message))
