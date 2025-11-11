"""GoodHome Integration pour Home Assistant."""
import logging
import asyncio
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers import discovery

from .goodhome_api import GoodHomeAPI

_LOGGER = logging.getLogger(__name__)

DOMAIN = "goodhome"
PLATFORMS = [Platform.CLIMATE, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.SELECT]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the GoodHome component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    
    if DOMAIN not in config:
        return True
    
    conf = config[DOMAIN]
    user_id = conf.get("user_id")
    token = conf.get("token")
    email = conf.get("email")
    password = conf.get("password")
    
    if (user_id and token) or (email and password):
        api = GoodHomeAPI(user_id, token, email, password)
        
        # Si email/password fournis, obtenir un nouveau token
        if email and password and not token:
            await hass.async_add_executor_job(api.login)
        
        async def async_update_data():
            """Fetch data from API."""
            try:
                devices = await hass.async_add_executor_job(api.get_devices)
                return devices
            except Exception as err:
                raise UpdateFailed(f"Error communicating with API: {err}")
        
        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name="goodhome",
            update_method=async_update_data,
            update_interval=timedelta(seconds=60),
        )
        
        # Pour une configuration YAML, utiliser async_refresh au lieu de async_config_entry_first_refresh
        await coordinator.async_refresh()
        
        hass.data[DOMAIN]["coordinator"] = coordinator
        hass.data[DOMAIN]["api"] = api
        
        # Register identify service
        async def async_identify_device(call):
            """Handle the identify device service call."""
            device_id = call.data.get("device_id")
            if device_id:
                await hass.async_add_executor_job(api.identify_device, device_id)
        
        hass.services.async_register(DOMAIN, "identify_device", async_identify_device)
        
        # Charger les plateformes
        for platform in PLATFORMS:
            hass.async_create_task(
                discovery.async_load_platform(hass, platform, DOMAIN, {}, config)
            )
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GoodHome from a config entry."""
    email = entry.data.get("email")
    password = entry.data.get("password")
    user_id = entry.data.get("user_id")
    token = entry.data.get("token")
    
    # Priorité à email/password si disponibles
    if email and password:
        api = GoodHomeAPI(None, None, email, password)
        # Obtenir le token
        await hass.async_add_executor_job(api.login)
    else:
        api = GoodHomeAPI(user_id, token)
    
    async def async_update_data():
        """Fetch data from API."""
        try:
            devices = await hass.async_add_executor_job(api.get_devices)
            return devices
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
    
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="goodhome",
        update_method=async_update_data,
        update_interval=timedelta(seconds=60),
    )
    
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
