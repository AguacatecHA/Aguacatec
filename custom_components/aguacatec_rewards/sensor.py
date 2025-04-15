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
            urlAguacoins = f"https://docs.google.com/spreadsheets/d/{self._idSpreadsheet}/export?format=csv&id={self._idSpreadsheet}&gid=0"
            async with self._session.get(urlAguacoins) as response:
                if response.status != 200:
                    _LOGGER.error(f"Error fetching data: {response.status}")
                    return None
                text = await response.text()
            urlSorteo = f"https://docs.google.com/spreadsheets/d/{self._idSpreadsheet}/export?format=csv&id={self._idSpreadsheet}&gid=809535125"
            async with self._session.get(urlSorteo) as response:
                if response.status != 200:
                    _LOGGER.error(f"Error fetching data: {response.status}")
                    return None
                textSorteo = await response.text()

        except Exception as e:
            _LOGGER.error(f"Exception fetching data: {e}")
            return None

        aguacoins_result = None
        lines = text.splitlines()
        if len(lines) < 2:
            aguacoins_result = None
        else:
            headers = lines[0].split(',')
            for line in lines[1:]:
                values = line.split(',')
                if values[0] == self._username:
                    aguacoins_result = dict(zip(headers[1:], values[1:]))  # Excluye "Usuario Telegram"
                    break

        numeros_sorteos = []
        lines = textSorteo.splitlines()
        if len(lines) < 2:
            numeros_sorteos = []
        else:
            headers = lines[0].split(',')
            for line in lines[1:]:
                values = line.split(',')
                if len(values) >= 2 and values[1] == self._username:  # Columna B es el nombre de usuario
                    numeros_sorteos.append(values[0])  # Columna A es el ID                    
            attributes_sorteo = {}
            for i in [2, 3, 4]: 
                values = lines[i].split(',')
                attr_name = values[3].strip() if len(values) > 3 and values[3] else None
                if attr_name:  # Solo procesar si el nombre del atributo no está vacío
                    # Obtener valor de columna E (índice 4), o "Vacio" si no existe o está vacío
                    attr_value = values[4].strip() if len(values) > 4 and values[4].strip() else "Vacio"
                    attributes_sorteo[attr_name] = attr_value
        if aguacoins_result is None and not numeros_sorteos and not attributes_sorteo:
            return None

        # Combinar resultados
        result = aguacoins_result or {}
        if numeros_sorteos:
            result['Numeros Sorteo'] = numeros_sorteos
        if attributes_sorteo:
            result.update(attributes_sorteo)  
        return result

    async def async_update(self):
        data = await self._fetch_data()
        if data:
            self._state = data.get("Aguacoins", "No hay datos")  # Estado principal: Aguacoins
            self._attributes = data  # Otros valores como atributos
        else:
            self._state = "Usuario no Encontrado"
            self._attributes = {}