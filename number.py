"""Support for GoodHome Number entities."""
import logging
import asyncio

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import POLLING_MAX_ATTEMPTS, POLLING_INTERVAL

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the GoodHome number platform (YAML config)."""
    coordinator = hass.data["goodhome"]["coordinator"]
    api = hass.data["goodhome"]["api"]
    
    devices = coordinator.data
    entities = []
    
    for device in devices:
        # Comfort Temperature
        entities.append(
            GoodHomeTemperatureNumber(
                coordinator,
                api,
                device,
                "comfTemp",
                "comfort_temperature",
                "mdi:home-thermometer",
            )
        )
        # Eco Temperature
        entities.append(
            GoodHomeTemperatureNumber(
                coordinator,
                api,
                device,
                "ecoTemp",
                "eco_temperature",
                "mdi:leaf",
            )
        )
        # Antifreeze Temperature
        entities.append(
            GoodHomeTemperatureNumber(
                coordinator,
                api,
                device,
                "antifTemp",
                "antifreeze_temperature",
                "mdi:snowflake",
            )
        )
    
    async_add_entities(entities, True)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the GoodHome number platform (config entry)."""
    coordinator = hass.data["goodhome"][entry.entry_id]["coordinator"]
    api = hass.data["goodhome"][entry.entry_id]["api"]
    
    devices = coordinator.data
    entities = []
    
    for device in devices:
        # Comfort Temperature
        entities.append(
            GoodHomeTemperatureNumber(
                coordinator,
                api,
                device,
                "comfTemp",
                "comfort_temperature",
                "mdi:home-thermometer",
            )
        )
        # Eco Temperature
        entities.append(
            GoodHomeTemperatureNumber(
                coordinator,
                api,
                device,
                "ecoTemp",
                "eco_temperature",
                "mdi:leaf",
            )
        )
        # Antifreeze Temperature
        entities.append(
            GoodHomeTemperatureNumber(
                coordinator,
                api,
                device,
                "antifTemp",
                "antifreeze_temperature",
                "mdi:snowflake",
            )
        )
    
    async_add_entities(entities, True)

class GoodHomeTemperatureNumber(CoordinatorEntity, NumberEntity):
    """Representation of a GoodHome Temperature Number."""
    
    def __init__(self, coordinator, api, device, parameter_name, translation_key, icon):
        """Initialize the number."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device["id"]
        self._device_name = device["name"]
        self._parameter_name = parameter_name
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._attr_unique_id = f"goodhome_{device['id']}_{parameter_name}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_mode = NumberMode.BOX
        self._attr_native_step = 0.5
        
        # Limites communes à tous les types de température : 7-30°C
        self._attr_native_min_value = 7.0
        self._attr_native_max_value = 30.0
        
        self._optimistic_value = None
        
    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {("goodhome", self._device_id)},
            "name": self._device_name,
            "manufacturer": "GoodHome",
            "model": "Thermostat",
        }
    
    def _get_device(self):
        """Get device from coordinator data."""
        for device in self.coordinator.data:
            if device["id"] == self._device_id:
                return device
        return None
    
    @property
    def available(self):
        """Return True if entity is available."""
        device = self._get_device()
        if device:
            return device.get("connected", False)
        return False
    
    @property
    def native_value(self):
        """Return the current value."""
        # Si on a une valeur optimiste, l'utiliser
        if self._optimistic_value is not None:
            return self._optimistic_value
        
        device = self._get_device()
        if device and device.get("state"):
            state = device["state"]
            return state.get(self._parameter_name)
        return None
    
    async def async_set_native_value(self, value: float) -> None:
        """Set new temperature value."""
        try:
            # État optimiste
            self._optimistic_value = value
            self.async_write_ha_state()
            
            # Envoyer la commande à l'API
            success = await self.hass.async_add_executor_job(
                self._api.set_temperature,
                self._device_id,
                self._parameter_name,
                value
            )
            
            if success:
                # Polling pour confirmer le changement
                for attempt in range(POLLING_MAX_ATTEMPTS):
                    await asyncio.sleep(POLLING_INTERVAL)
                    await self.coordinator.async_request_refresh()
                    
                    device = self._get_device()
                    if device and device.get("state"):
                        current_value = device["state"].get(self._parameter_name)
                        if current_value == value:
                            _LOGGER.info(f"Temperature {self._parameter_name} confirmed: {value}°C")
                            self._optimistic_value = None
                            self.async_write_ha_state()
                            return
                
                # Si après 40s pas de confirmation, on garde l'état optimiste
                _LOGGER.warning(f"Temperature {self._parameter_name} not confirmed after {POLLING_MAX_ATTEMPTS * POLLING_INTERVAL}s, keeping optimistic state")
            else:
                # Échec de l'API, annuler l'état optimiste
                self._optimistic_value = None
                self.async_write_ha_state()
                _LOGGER.error(f"Failed to set {self._attr_name}")
                
        except Exception as err:
            # En cas d'erreur, annuler l'état optimiste
            self._optimistic_value = None
            self.async_write_ha_state()
            _LOGGER.error(f"Error setting {self._attr_name}: {err}")
    
    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        device = self._get_device()
        if device and device.get("state"):
            state = device["state"]
            attrs = {
                "parameter": self._parameter_name,
                "target_temp": state.get("targetTemp"),
                "current_temp": state.get("currentTemp"),
            }
            
            # Ajouter des infos contextuelles
            if self._parameter_name == "comfTemp":
                attrs["description"] = "Température de consigne en mode Confort"
            elif self._parameter_name == "ecoTemp":
                attrs["description"] = "Température de consigne en mode Économie d'énergie"
            elif self._parameter_name == "antifTemp":
                attrs["description"] = "Température de consigne en mode Hors-gel (OFF)"
                
            return attrs
        return {}
