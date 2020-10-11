import asyncio
import json
from logging import getLogger
import queue
import threading
import time

import paho.mqtt.client as paho

_LOGGER = getLogger(__name__)

class Hub:
    def __init__(self, hass, host, port):
        self.host = host
        self.port = port
        self._hass = hass
        self.remote_commands = []
        self.entities = []
        self.running = False
        self._has_config = False

    def add_platform(self, entity):
        self.entities.append(entity)

    async def test_connection(self):
        """Test connectivity to the Dummy hub is OK."""
        await asyncio.sleep(1)
        return True

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
            self.client.subscribe([("state/#", 0)])

        return self._has_config

    async def stop(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as ex:
            pass

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

    def _on_message(self, client, userdata, message):
        try:
            self._handle_message(message)
        except Exception as msg:
            _LOGGER.exception("Failed to parse message from device:" + msg)

    def _handle_message(self, message):
        _LOGGER.info(message)

        if message.topic.startswith('state'):
            driver_name = message.topic.split('/')[1]
            self._handle_topic_state(driver_name, json.loads(message.payload))

        if message.topic == 'config':
            self._handle_topic_config(json.loads(message.payload))

    def _handle_topic_state(self, driver_name, payload):
        if driver_name == 'xxx':
            pass

    def _handle_topic_config(self, payload):
        self.remote_commands = payload['remoteIR']['commands'] or []
        self._has_config = True
    
    def send_command(self, topic, message):
        self.client.publish(f"{topic}", json.dumps(message))
