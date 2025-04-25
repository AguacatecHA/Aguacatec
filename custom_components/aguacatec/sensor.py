import logging
from aiohttp import ClientSession
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Definir los campos y sus íconos
CAMPOS_SENSORES = {
    "Categoría": {"nombre": "Categoría", "icono": "mdi:egg-outline"},
    "Suscripción": {"nombre": "Suscripción", "icono": "mdi:calendar-sync"},
    "Aguacoins": {"nombre": "Aguacoins", "icono": "mdi:checkbox-multiple-blank-circle"},
    "Sesiones Extra": {"nombre": "Sesiones Extra", "icono": "mdi:lifebuoy"},
    "Tarjetas": {"nombre": "Tarjetas", "icono": "mdi:palette"},
    "Numeros Sorteo": {"nombre": "Números Sorteo", "icono": "mdi:ticket"},
    "Fecha último sorteo": {"nombre": "Fecha Último Sorteo", "icono": "mdi:calendar-star"},
    "Nº premiado": {"nombre": "Número Premiado", "icono": "mdi:trophy"},
    "Ganador": {"nombre": "Ganador", "icono": "mdi:party-popper"},
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    config = hass.data[DOMAIN][entry.entry_id]
    # Crear una instancia para obtener datos compartida entre sensores
    data_fetcher = AguacatecDataFetcher(hass, config)
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
        sw_version="0.0.5",
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
        self._session = async_get_clientsession(hass)
        self.datos = None

    async def _obtener_datos(self):
        try:
            # Obtener datos de Aguacoins
            urlAguacoins = f"https://docs.google.com/spreadsheets/d/{self._idSpreadsheet}/export?format=csv&id={self._idSpreadsheet}&gid=0"
            async with self._session.get(urlAguacoins) as respuesta:
                if respuesta.status != 200:
                    _LOGGER.error(f"Error al obtener datos de Aguacoins: {respuesta.status}")
                    return None
                texto = await respuesta.text()

            # Obtener Numeros del Sorteo
            urlSorteo = f"https://docs.google.com/spreadsheets/d/{self._idSpreadsheet}/export?format=csv&id={self._idSpreadsheet}&gid=809535125"
            async with self._session.get(urlSorteo) as respuesta:
                if respuesta.status != 200:
                    _LOGGER.error(f"Error al obtener los numeros del Sorteo: {respuesta.status}")
                    return None
                texto_sorteo = await respuesta.text()

            # Obtener Datos del Sorteo
            datosSorteo = f"https://docs.google.com/spreadsheets/d/{self._idSpreadsheet}/export?format=csv&id={self._idSpreadsheet}&gid=992544740"
            async with self._session.get(datosSorteo) as respuesta:
                if respuesta.status != 200:
                    _LOGGER.error(f"Error al obtener datos de Sorteo: {respuesta.status}")
                    return None
                datos_sorteo = await respuesta.text()





        except Exception as e:
            _LOGGER.error(f"Excepción al obtener datos: {e}")
            return None

        # Procesar datos de Aguacoins
        resultado_aguacoins = None
        lineas = texto.splitlines()
        if len(lineas) >= 2:
            cabeceras = lineas[0].split(',')
            for linea in lineas[1:]:
                valores = linea.split(',')
                if valores[0] == self._usuario:
                    resultado_aguacoins = dict(zip(cabeceras[1:], valores[1:]))  # Excluye "Usuario Telegram"
                    break

        # Procesar datos de Sorteo
        numeros_sorteos = []
        lineas = texto_sorteo.splitlines()
        if len(lineas) >= 2:
            cabeceras = lineas[0].split(',')
            for linea in lineas[1:]:
                valores = linea.split(',')
                if len(valores) >= 2 and self._usuario in valores[1]:
                    numeros_sorteos.append(valores[0])  # Columna A es el ID


        # Procesar datos de Atributos del Sorteo
        atributos_sorteo = {}
        lineas = datos_sorteo.splitlines()
        if len(lineas) >= 2:
            for linea in lineas[1:]:  # Empezar desde la segunda fila (ignorar encabezado)
                valores = linea.split(',')
                if len(valores) >= 2:
                    nombre_atributo = valores[0].strip()  # Columna A (Dato)
                    if nombre_atributo and nombre_atributo in CAMPOS_SENSORES:
                        valor_atributo = valores[1].strip() if len(valores) > 1 and valores[1].strip() else "Vacio"
                        atributos_sorteo[nombre_atributo] = valor_atributo

        if resultado_aguacoins is None and not numeros_sorteos and not atributos_sorteo:
            return None

        # Combinar resultados
        resultado = resultado_aguacoins or {}
        if numeros_sorteos:
            resultado['Numeros Sorteo'] = numeros_sorteos
        if atributos_sorteo:
            resultado.update(atributos_sorteo)
        return resultado

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
        self._attr_unique_id = f"{DOMAIN}_{usuario}_{clave.lower().replace(' ', '_')}"
        self._attr_icon = icono
        self._attr_device_info = device_info  # Vincular al dispositivo
        self._attr_scan_interval = 60  # Actualizar cada 60 segundos

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
