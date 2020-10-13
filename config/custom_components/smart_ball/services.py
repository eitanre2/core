import asyncio

from homeassistant.core import HomeAssistant

from .const import DOMAIN


def register_global_services(hass: HomeAssistant):
    def glboal_play_IR_Remote_command(call):
        command_name = call.data.get('command_name')
        hub_id = call.data.get('hub_id')

        if command_name is None or hub_id is None:
            return
        command_name = str(command_name)
        select_hub = None
        for h in hub.HUBS:
            if hub.HUBS[h].hub_id == hub_id:
                select_hub = hub.HUBS[h]
                break
        if select_hub is not None:
            for entity in select_hub.entities:
                if entity.command == command_name:
                    entity.turn_on()
                    break

    hass.services.async_register(DOMAIN, f'smart_ball_play_IR_Remote_command', glboal_play_IR_Remote_command)

def register_services(hub, hass: HomeAssistant):
    def run_IR_Remote_command(call):
        entity_id = call.data.get('entity_id')
        if entity_id is None:
            return
        for entity in hub.entities:
            if entity.entity_id == entity_id:
                entity.turn_on()

    def record_IR_Remote_command(call):
        command_name = call.data.get('command_name')
        if command_name is None:
            return
        command_name = str(command_name)
        found = False
        for entity in hub.entities:
            if entity.command == command_name:
                found = True
        if not found:
            asyncio.run(hub.remote_start_record(command_name))

    hass.services.async_register(DOMAIN, f'{hub.hub_id}_run_IR_Remote_command', run_IR_Remote_command)
    hass.services.async_register(DOMAIN, f'{hub.hub_id}_record_IR_Remote_command', record_IR_Remote_command)
