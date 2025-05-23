# 🥑 Componente Aguacatec 🥑
## ¿Que puede hacer este Componente Aguacatec?

«Aguacatec» Es un componente para [Home Assistant](https://home-assistant.io/) que permite obtener los beneficios de tu suscripcion de Aguacatec para visualizarlo en tu instalación de Home Assistant, y asi tener toda la información actualizada.


### Mediante HACS (Recomendado)

Para instalar el componente usando HACS:

1. Haz Click en los tres puntos en la parte de arriba de la esquina del menu de HACKS.
2. Selecciona **Repositorio Personalizado**.
3. Añade la URL del repositorio: `https://github.com/AguacatecHA/Aguacatec`.
4. Seleciona el tipo: **Integracion**.
5. Haz click en el boton **Añadir**.

<details>
<summary>Fuera de HACS</summary>

1. Descarga la ultima release de la integracion Aguacatec de **[GitHub Releases](https://github.com/AguacatecHA/Aguacatec/releases)**.
2. Extrae de la descarga los ficheros y pon la carpeta `aguacatec` en la carpeta `custom_components` de tu Home Assistant (usualmente localizada dentro de `config/custom_components`).
3. Reinicia tu Home Assistant para cargar la nueva integracion.

</details>

## Configuracion

Para añadir la integracion a tu instancia de Home Assistant, usa el boton:

<p>
    <a href="https://my.home-assistant.io/redirect/config_flow_start?domain=aguacatec" class="my badge" target="_blank">
        <img src="https://my.home-assistant.io/badges/config_flow_start.svg">
    </a>
</p>



### Configuration Manual

Una vez instalado, ve a _Dispositivos y Servicios -> Añadir Integración_ y busca _Aguacatec_.

![image](https://github.com/user-attachments/assets/f43a726d-5779-43ae-8b0f-b6013d7a314c)

El asistente te irá solicitando los datos, como el ID que recibiste cuando te hiciste patreon y tu nombre de usuario de telegram, si no conoces alguno de los datos preguntame en [Telegram](https://t.me/aguacatec_es)

![image](https://github.com/user-attachments/assets/58755dc0-10bc-4aa3-9686-4021fcac3cdd)


Una vez configurado, tendrás la integración con la entidad de tu nombre de usuario y los sensores con toda tu informacion. 

![image](https://github.com/user-attachments/assets/76e20047-d241-4379-bbda-1ee63ad804eb)
