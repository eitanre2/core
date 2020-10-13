import logging
import re

import voluptuous as vol

from homeassistant import config_entries, core, exceptions

from .const import DOMAIN
from .hub import Hub

_LOGGER = logging.getLogger(__name__)

IP_REGEX = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

DATA_SCHEMA = vol.Schema({vol.Required("name", msg="name", default="My Smart Ball"): str,
                          vol.Required("host", msg="host", default=None): str,
                          vol.Required("port", msg="port", default=1883): int})

async def validate_input(hass: core.HomeAssistant, data: dict):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    # Validate the data can be used to set up a connection.

    # This is a simple example to show an error in the UI for a short hostname
    # The exceptions are defined at the end of this file, and are used in the
    # `async_step_user` method below.
    if data["host"] is None or not IP_REGEX.match(data["host"]):
        raise InvalidHost

    if data["name"] is None or len(data["name"]) < 1:
        raise InvalidName

    for entry in hass.config_entries.async_entries():
        if entry.domain != DOMAIN:
            continue
        if entry.data['name'] == data['name'] or entry.data['host'] == data['host']:
            raise MustBeUniqueBall
        

    hub = Hub(hass, data, data["name"], data["host"], data["port"])
    result = await hub.test_connection()

    if not result:
        # If there is an error, raise an exception to notify HA that there was a
        # problem. The UI will also show there was a problem
        raise CannotConnect

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    return {"title": f"Smart Ball-{data['name']}-{hub.hub_id_short} ({data['host']}:{data['port']})" }

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # This goes through the steps to take the user through the setup process.
        # Using this it is possible to update the UI and prompt for additional
        # information. This example provides a single form (built from `DATA_SCHEMA`),
        # and when that has some validated input, it calls `async_create_entry` to
        # actually create the HA config entry. Note the "title" value is returned by
        # `validate_input` above.
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                # The error string is set here, and should be translated.
                # This example does not currently cover translations, see the
                # comments on `DATA_SCHEMA` for further details.
                # Set the error on the `host` field, not the entire form.
                errors["host"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id='user', data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""

class InvalidName(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hub name."""

class MustBeUniqueBall(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hub name."""
