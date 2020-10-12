import asyncio
import hashlib
import json
from logging import getLogger
import queue
import threading
from threading import Timer
import time

import paho.mqtt.client as paho

from . import const

_LOGGER = getLogger(__name__)

HUBS = {}
COMMON_DEVICES = [  const.DEVICE_CLASS_TEMPERATURE, 
                    const.DEVICE_CLASS_HUMIDITY, 
                    const.DEVICE_CLASS_LDR, 
                    const.DEVICE_CLASS_MOTION, 
                    const.DEVICE_CLASS_UPTIME,
                    const.DEVICE_CLASS_MOTION_BINARY,
                    const.DEVICE_CLASS_IRRemote_BINARY]
class Hub:
    def __init__(self, hass, name, host, port):
        self.host = host
        self.port = port or 1883
        self._hass = hass
        self._name = name
        self._hub_id = None
        self._has_config = False
        self.remote_commands = []
        self.entities = []
        self.running = False

    def add_platform(self, entity):
        self.entities.append(entity)

    @property
    def name(self):
        return self._name

    @property
    def hub_id(self):
        return self._hub_id

    async def connect(self):
        self.running = True
        self.pending_tasks_queue = queue.Queue()
        self.queue_thread = threading.Thread(target = self._queue_routine)
        self.queue_thread.start()

        try:
            self.client = paho.Client()
            self.client.on_message = self._on_message
            self.client.connect(self.host, port = int(self.port))
        except Exception as ex:
            self.running = False
            return False

        # get ready for new messages
        self.client.loop_start()
        # ask for config
        self.client.subscribe([("config/#", 0)])

        limit = 10
        _LOGGER.info("Waiting to device config..")
        while not self._has_config and limit > 0:
            await asyncio.sleep(1)
            limit = limit - 1

        if not self._has_config:
            await self.stop()
        else:
            self._start()

        return self._has_config

    async def stop(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as ex:
            pass

    async def remote_command(self, command_name):
        self.send_command('scenes/IR_scene/command', {"name":"play", "code": command_name})

    async def remote_start_record(self, command_name):
        self.send_command('scenes/IR_scene/command', {"name":"record", "code": command_name})

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

    def _start(self):
        HUBS[self.hub_id] = self
        self.client.subscribe([("state/#", 0)])

        self._timer = Timer(const.REFRESH_INTERVAL, self.timer_callback)
        self._timer.start()

    def timer_callback(self):
        if self.running == False:
            return

        for entity in self.entities:
            if hasattr(entity, 'should_poll_frequently') and entity.should_poll_frequently:
                entity.schedule_update_ha_state(True)


        self._timer = Timer(const.REFRESH_INTERVAL, self.timer_callback)
        self._timer.start()

    def _on_message(self, client, userdata, message):
        try:
            self._handle_message(message)
        except Exception as msg:
            _LOGGER.exception("Failed to parse message from device:" + msg)

    def _handle_message(self, message):
        _LOGGER.info(f"MQTT message. topic={message.topic}")

        if message.topic.startswith('state'):
            message_json = json.loads(message.payload)
            for device in message_json['devices']:
                try:
                    self._handle_topic_state(device['name'], device['data'])
                except Exception as msg:
                 _LOGGER.exception(f"Failed to update device ({device['name']}) value :" + msg)

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
        self.remote_commands = payload['remoteIR']['commands'] or []
        self._hub_id = payload["hub_id"]
        self._has_config = True
    
    def send_command(self, topic, message):
        self.client.publish(f"{topic}", json.dumps(message))
