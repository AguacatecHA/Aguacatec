# custom_components/aguacatec_rewards/__init__.py

import logging

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

async def async_setup(hass: HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Setting up entry for Aguacatec: %s", entry.title)

    # Guardamos la información de la entry en hass.data si hace falta.
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Si tu integración expone, por ejemplo, la plataforma "sensor":
    await hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Unloading entry for Aguacatec: %s", entry.title)

    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    # Limpia lo que corresponda de hass.data si hace falta
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok