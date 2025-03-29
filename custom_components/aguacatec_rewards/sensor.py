import logging
from aiohttp import ClientSession
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry  # Importación añadida

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    config = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AguacatecUserSensor(hass, config)])

class AguacatecUserSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, config):
        self.hass = hass
        self._username = config["user_telegram"]
        self._idSpreadsheet = config["id_aguacatec"]
        self._state = None
        self._attributes = {}
        self._attr_name = f"Aguacatec Rewards {self._username}"
        self._attr_unique_id = f"{DOMAIN}_{self._username}"
        self._attr_scan_interval = 10  # Actualiza cada 60 segundos
        self._session = async_get_clientsession(hass)  # Usa la sesión de HA
 
    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def _fetch_data(self):
        try:        
            url = f"https://docs.google.com/spreadsheets/d/{self._idSpreadsheet}/gviz/tq?tqx=out:csv&sheet=Sheet1"
            async with self._session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error(f"Error fetching data: {response.status}")
                    return None
                text = await response.text()
        except Exception as e:
            _LOGGER.error(f"Exception fetching data: {e}")
            return None

        lines = text.splitlines()
        if len(lines) < 2:
            return None

        headers = lines[0].strip('"').split('","')
        for line in lines[1:]:
            values = line.strip('"').split('","')
            if values[0] == self._username:
                return dict(zip(headers[1:], values[1:]))  # Excluye "Usuario Telegram"
        return None

    async def async_update(self):
        data = await self._fetch_data()
        if data:
            self._state = data.get("Aguacoins", "No data")  # Estado principal: Aguacoins
            self._attributes = data  # Otros valores como atributos
        else:
            self._state = "User not found"
            self._attributes = {}