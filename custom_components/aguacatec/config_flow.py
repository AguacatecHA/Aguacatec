# custom_components/aguacatec/config_flow.py
import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN  # asumes que en const.py tienes DOMAIN = "aguacatec"

@config_entries.HANDLERS.register(DOMAIN)
class aguacatecConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1


    async def async_step_user(self, user_input=None):
        """Paso inicial cuando el usuario añade la integración desde la UI."""
        errors = {}
        description = (
            "Esta integración te da tus beneficios y numeros de sorteo de la comunidad Aguacatec. "
            "Por favor, ingresa tu nombre de usuario de telegram, el que viene con @."
        )
        if user_input is not None:
            # Aquí podrías validar la key haciendo una llamada a la API,
            # o simplemente aceptarla directamente.
            app_id   = user_input["id_aguacatec"]
            app_name = user_input["user_telegram"]
            
            # Supongamos que NO validamos la API key en la creación (podrías hacerlo)
            # y simplemente la guardamos en el Config Entry.
            return self.async_create_entry(title={app_name}, data=user_input)

        # Si no hay `user_input` todavía, mostramos el formulario.
        data_schema = vol.Schema(
            {
                vol.Required("id_aguacatec"): cv.string,
                vol.Required("user_telegram"): cv.string,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"model": description},
        )