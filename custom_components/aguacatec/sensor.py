import logging
import asyncio
import csv
from aiohttp import ClientSession
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from async_timeout import timeout

from . import DOMAIN, VERSION

_LOGGER = logging.getLogger(__name__)

# Definir los campos y sus íconos
CAMPOS_SENSORES = {
    "Categoría": {"nombre": "Categoría", "icono": "mdi:egg-outline"},
    "Suscripción": {"nombre": "Suscripción", "icono": "mdi:calendar-sync"},
    "Aguacoins": {"nombre": "Aguacoins", "icono": "mdi:checkbox-multiple-blank-circle"},
    "Sesiones Extra": {"nombre": "Sesiones Extra", "icono": "mdi:lifebuoy"},
    "Tarjetas": {"nombre": "Tarjetas", "icono": "mdi:palette"},
    "Premio": {"nombre": "Sorteo Premiado", "icono": "mdi:trophy-award"},
    "Numeros Sorteo": {"nombre": "Números Sorteo", "icono": "mdi:ticket"},
    "Fecha último sorteo": {"nombre": "Fecha Último Sorteo", "icono": "mdi:calendar-star"},
    "Fecha próximo sorteo": {"nombre": "Fecha Próximo Sorteo", "icono": "mdi:calendar"},
    "Nº premiado": {"nombre": "Número Premiado", "icono": "mdi:trophy"},
    "Ganador": {"nombre": "Ultimo Ganador", "icono": "mdi:party-popper"},
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    config = hass.data[DOMAIN][entry.entry_id]
    # Crear una instancia para obtener datos compartida entre sensores
    data_fetcher = AguacatecDataFetcher(hass, config)
    await data_fetcher.async_init()  # Inicializar la sesión
    # Crear sensores basados en los campos definidos
    sensores = await crear_sensores(hass, config, data_fetcher)
    async_add_entities(sensores)

async def crear_sensores(hass: HomeAssistant, config: dict, data_fetcher):
    """Crear entidades de sensores basadas en los campos definidos."""
    usuario = config["user_telegram"]
    id_aguacatec = config["id_aguacatec"]
    # Obtener datos iniciales
    await data_fetcher.async_update()
    datos = data_fetcher.datos

    sensores = []
    # Definir información del dispositivo
    device_info = DeviceInfo(
        identifiers={(DOMAIN, f"{id_aguacatec}_{usuario}")},
        name=f"Aguacatec {usuario}",
        manufacturer="Aguacatec",
        model="Informacion de Aguacatec",
        sw_version=VERSION,
    )

    if datos:
        # Crear un sensor por cada campo definido
        for clave, info in CAMPOS_SENSORES.items():
            if clave in datos:  # Crear solo si el campo existe en los datos
                sensor = AguacatecSensor(hass, config, data_fetcher, clave, usuario, info["icono"], device_info)
                sensores.append(sensor)
    else:
        # Si no hay datos, crear solo el sensor de estado
        sensor = AguacatecSensor(hass, config, data_fetcher, "estado", usuario, "mdi:alert", device_info)
        sensores.append(sensor)
    return sensores

class AguacatecDataFetcher:
    """Clase para gestionar la obtención y compartición de datos entre sensores."""
    def __init__(self, hass: HomeAssistant, config):
        self.hass = hass
        self._usuario = config["user_telegram"]
        self._idSpreadsheet = config["id_aguacatec"]
        self._session = None  # Inicializar en async_init
        self.datos = None
        self._last_fetch_time = 0
        self._cache_duration = 600  # Cache de 10 minutos
        self._max_retries = 5  # Más reintentos para manejar errores 429
        self._base_delay = 3  # Retraso inicial más largo

    async def async_init(self):
        """Inicializa la sesión asíncrona."""
        self._session = async_get_clientsession(self.hass)

    async def _fetch_with_retry(self, url, retries=0):
        """Realiza una solicitud HTTP con reintentos en caso de fallo."""
        try:
            async with timeout(15):  # Timeout de 15 segundos por solicitud
                async with self._session.get(url) as respuesta:
                    if respuesta.status == 200:
                        return await respuesta.text()
                    elif respuesta.status == 429 and retries < self._max_retries:
                        delay = self._base_delay * (2 ** retries)  # Retraso exponencial
                        _LOGGER.warning(f"Error 429: Demasiadas solicitudes para {url}. Reintentando en {delay}s...")
                        await asyncio.sleep(delay)
                        return await self._fetch_with_retry(url, retries + 1)
                    else:
                        _LOGGER.error(f"Error al obtener datos desde {url}: {respuesta.status}")
                        return None
        except Exception as e:
            _LOGGER.error(f"Excepción al obtener datos desde {url}: {e}")
            return None

    async def _obtener_datos(self):
        """Obtiene datos de las hojas de cálculo con cacheo y reintentos."""
        # Verificar si los datos en caché son recientes
        current_time = self.hass.loop.time()
        if self.datos and (current_time - self._last_fetch_time) < self._cache_duration:
            _LOGGER.debug("Devolviendo datos desde caché")
            return self.datos

        resultado_aguacoins = None
        atributos_sorteo = {}
        numeros_sorteos = []

        try:
            # Obtener datos de Aguacoins
            url_aguacoins = f"https://docs.google.com/spreadsheets/d/{self._idSpreadsheet}/export?format=csv&id={self._idSpreadsheet}&gid=0"
            texto_aguacoins = await self._fetch_with_retry(url_aguacoins)
            if texto_aguacoins:
                reader = csv.reader(texto_aguacoins.splitlines())
                cabeceras = next(reader, None)  # Leer encabezados
                if cabeceras:
                    for row in reader:
                        if row and row[0] == self._usuario:
                            resultado_aguacoins = dict(zip(cabeceras[1:], row[1:]))
                            break
                else:
                    _LOGGER.warning("No se encontraron encabezados en los datos de Aguacoins")

            # Obtener Números del Sorteo
            url_sorteo = f"https://docs.google.com/spreadsheets/d/{self._idSpreadsheet}/export?format=csv&id={self._idSpreadsheet}&gid=809535125"
            texto_sorteo = await self._fetch_with_retry(url_sorteo)
            if texto_sorteo:
                reader = csv.reader(texto_sorteo.splitlines())
                cabeceras = next(reader, None)
                if cabeceras:
                    for row in reader:
                        if len(row) >= 2 and self._usuario in row[1]:
                            numeros_sorteos.append(row[0])
                else:
                    _LOGGER.warning("No se encontraron encabezados en los datos del Sorteo")

            # Obtener Datos del Sorteo
            url_datos_sorteo = f"https://docs.google.com/spreadsheets/d/{self._idSpreadsheet}/export?format=csv&id={self._idSpreadsheet}&gid=992544740"
            texto_datos_sorteo = await self._fetch_with_retry(url_datos_sorteo)
            if texto_datos_sorteo:
                reader = csv.reader(texto_datos_sorteo.splitlines())
                next(reader, None)  # Ignorar encabezado
                for row in reader:
                    if len(row) >= 2 and row[0].strip() in CAMPOS_SENSORES:
                        atributos_sorteo[row[0].strip()] = row[1].strip() if row[1].strip() else "Vacio"

            # Combinar resultados
            resultado = resultado_aguacoins or {}
            if numeros_sorteos:
                resultado['Numeros Sorteo'] = numeros_sorteos
            if atributos_sorteo:
                resultado.update(atributos_sorteo)

            # Almacenar datos en caché solo si se obtuvo algún dato
            if resultado:
                self.datos = resultado
                self._last_fetch_time = current_time
            else:
                _LOGGER.warning("No se obtuvieron datos nuevos; manteniendo caché anterior")
            
            return self.datos

        except Exception as e:
            _LOGGER.error(f"Excepción general al obtener datos: {e}")
            return self.datos  # Devolver datos en caché si existen

    async def async_update(self):
        """Actualizar los datos compartidos."""
        self.datos = await self._obtener_datos()

class AguacatecSensor(SensorEntity):
    """Sensor individual para cada parámetro de Aguacatec."""
    def __init__(self, hass: HomeAssistant, config: dict, data_fetcher: AguacatecDataFetcher, clave: str, usuario: str, icono: str, device_info: DeviceInfo):
        self.hass = hass
        self._data_fetcher = data_fetcher
        self._clave = clave
        self._usuario = usuario
        self._estado = None
        self._attr_name = f"{CAMPOS_SENSORES.get(clave, {'nombre': clave})['nombre']}"
        self._attr_unique_id = f"{DOMAIN}_{CAMPOS_SENSORES.get(clave, {'nombre': clave})['nombre'].lower().replace(' ', '_')}"
        self._attr_icon = icono
        self._attr_device_info = device_info  # Vincular al dispositivo
        self._attr_scan_interval = 600  # Actualizar cada 10 minutos

    @property
    def state(self):
        """Devuelve el estado del sensor."""
        return self._estado

    async def async_update(self):
        """Actualiza el estado del sensor."""
        await self._data_fetcher.async_update()
        datos = self._data_fetcher.datos
        if datos and self._clave in datos:
            valor = datos[self._clave]
            # Manejar listas (como Numeros Sorteo) uniéndolas con comas
            self._estado = ", ".join(valor) if isinstance(valor, list) else valor
        else:
            self._estado = "Usuario no Encontrado" if self._clave == "estado" else "Sin datos"
