"""Config flow pour GoodHome integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .goodhome_api import GoodHomeAPI

_LOGGER = logging.getLogger(__name__)

DOMAIN = "goodhome"

class GoodHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GoodHome."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Valider les credentials
            try:
                email = user_input[CONF_EMAIL]
                password = user_input[CONF_PASSWORD]
                
                # Tester la connexion
                api = GoodHomeAPI(None, None, email, password)
                success = await self.hass.async_add_executor_job(api.login)
                
                if success:
                    # Créer l'entrée de configuration
                    await self.async_set_unique_id(email)
                    self._abort_if_unique_id_configured()
                    
                    return self.async_create_entry(
                        title=f"GoodHome ({email})",
                        data={
                            CONF_EMAIL: email,
                            CONF_PASSWORD: password,
                        },
                    )
                else:
                    errors["base"] = "invalid_auth"
                    
            except Exception as e:
                _LOGGER.error(f"Error during config flow: {e}")
                errors["base"] = "cannot_connect"

        # Afficher le formulaire
        data_schema = vol.Schema({
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return GoodHomeOptionsFlow(config_entry)


class GoodHomeOptionsFlow(config_entries.OptionsFlow):
    """Handle options for GoodHome."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                # Ici tu peux ajouter des options configurables
                # Par exemple: intervalle de mise à jour, etc.
            }),
        )
