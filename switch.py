"""GoodHome Switch Platform."""
import logging
import asyncio

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import POLLING_MAX_ATTEMPTS, POLLING_INTERVAL

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the GoodHome switch platform (YAML config)."""
    coordinator = hass.data["goodhome"]["coordinator"]
    api = hass.data["goodhome"]["api"]
    
    devices = coordinator.data
    entities = []
    
    for device in devices:
        # Open Window Detection switch (API parameter: window)
        entities.append(
            GoodHomeSwitch(
                coordinator,
                api,
                device,
                "window",
                "Open Window Detection",
                "mdi:window-open-variant",
            )
        )
        # Presence Sensor switch (API parameter: occupancyStatus)
        entities.append(
            GoodHomeSwitch(
                coordinator,
                api,
                device,
                "occupancyStatus",
                "Presence Sensor",
                "mdi:account-check",
            )
        )
        # Self Learning switch (API parameter: selfLearning)
        entities.append(
            GoodHomeSwitch(
                coordinator,
                api,
                device,
                "selfLearning",
                "Self Learning",
                "mdi:school",
            )
        )
        # Manual Mode switch (API parameter: noprog)
        entities.append(
            GoodHomeSwitch(
                coordinator,
                api,
                device,
                "noprog",
                "Manual Mode",
                "mdi:hand-back-right",
            )
        )
    
    async_add_entities(entities, True)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the GoodHome switch platform (config entry)."""
    coordinator = hass.data["goodhome"][entry.entry_id]["coordinator"]
    api = hass.data["goodhome"][entry.entry_id]["api"]
    
    devices = coordinator.data
    entities = []
    
    for device in devices:
        # Open Window Detection switch (API parameter: window)
        entities.append(
            GoodHomeSwitch(
                coordinator,
                api,
                device,
                "window",
                "Open Window Detection",
                "mdi:window-open-variant",
            )
        )
        # Presence Sensor switch (API parameter: occupancyStatus)
        entities.append(
            GoodHomeSwitch(
                coordinator,
                api,
                device,
                "occupancyStatus",
                "Presence Sensor",
                "mdi:account-check",
            )
        )
        # Self Learning switch (API parameter: selfLearning)
        entities.append(
            GoodHomeSwitch(
                coordinator,
                api,
                device,
                "selfLearning",
                "Self Learning",
                "mdi:school",
            )
        )
        # Manual Mode switch (API parameter: noprog)
        entities.append(
            GoodHomeSwitch(
                coordinator,
                api,
                device,
                "noprog",
                "Manual Mode",
                "mdi:hand-back-right",
            )
        )
    
    async_add_entities(entities, True)

class GoodHomeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a GoodHome Switch."""
    
    def __init__(self, coordinator, api, device, parameter_name, switch_name, icon):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device["id"]
        self._device_name = device["name"]
        self._parameter_name = parameter_name
        self._attr_name = f"{device['name']} {switch_name}"
        self._attr_unique_id = f"goodhome_{device['id']}_{parameter_name}"
        self._attr_icon = icon
        # Pas de assumed_state pour avoir un vrai toggle comme Hue
        # On gère l'état optimiste différemment
        self._optimistic_state = None  # État local temporaire
        
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
    def is_on(self):
        """Return true if the switch is on."""
        # Si on a un état optimiste (commande récente), l'utiliser
        if self._optimistic_state is not None:
            return self._optimistic_state
        
        # Sinon, utiliser l'état de l'API
        device = self._get_device()
        if device and device.get("state"):
            state = device["state"]
            # Convertir la valeur API en booléen
            value = state.get(self._parameter_name)
            if isinstance(value, bool):
                return value
            elif isinstance(value, (int, str)):
                # Gérer les valeurs "0"/"1" ou 0/1
                return str(value) == "1" or value == 1 or str(value).lower() == "true"
        return False
    
    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        try:
            # Définir l'état optimiste immédiatement
            self._optimistic_state = True
            self.async_write_ha_state()
            
            # Envoyer la commande à l'API
            success = await self.hass.async_add_executor_job(
                self._api.set_parameter,
                self._device_id,
                self._parameter_name,
                True
            )
            
            if success:
                # Attendre que le thermostat traite la commande (jusqu'à 40 secondes)
                # Faire plusieurs tentatives pour confirmer le changement
                for attempt in range(POLLING_MAX_ATTEMPTS):
                    await asyncio.sleep(POLLING_INTERVAL)
                    await self.coordinator.async_request_refresh()
                    
                    # Vérifier si l'état de l'API correspond à notre commande
                    device = self._get_device()
                    if device and device.get("state"):
                        api_value = device["state"].get(self._parameter_name)
                        if api_value is True or api_value == 1:
                            # État confirmé par l'API, on peut abandonner l'état optimiste
                            _LOGGER.info(f"{self._attr_name} turned on confirmed after {(attempt+1)*POLLING_INTERVAL}s")
                            self._optimistic_state = None
                            self.async_write_ha_state()
                            return
                
                # Après le timeout, abandonner l'état optimiste même sans confirmation
                _LOGGER.warning(f"{self._attr_name} turn on not confirmed after 30s, assuming success")
                self._optimistic_state = None
                self.async_write_ha_state()
            else:
                # En cas d'échec, annuler l'état optimiste
                self._optimistic_state = None
                self.async_write_ha_state()
                _LOGGER.error(f"Failed to turn on {self._attr_name}")
                
        except Exception as err:
            # En cas d'erreur, annuler l'état optimiste
            self._optimistic_state = None
            self.async_write_ha_state()
            _LOGGER.error(f"Error turning on {self._attr_name}: {err}")
    
    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        try:
            # Définir l'état optimiste immédiatement
            self._optimistic_state = False
            self.async_write_ha_state()
            
            # Envoyer la commande à l'API
            success = await self.hass.async_add_executor_job(
                self._api.set_parameter,
                self._device_id,
                self._parameter_name,
                False
            )
            
            if success:
                # Attendre que le thermostat traite la commande (jusqu'à 40 secondes)
                # Faire plusieurs tentatives pour confirmer le changement
                for attempt in range(POLLING_MAX_ATTEMPTS):
                    await asyncio.sleep(POLLING_INTERVAL)
                    await self.coordinator.async_request_refresh()
                    
                    # Vérifier si l'état de l'API correspond à notre commande
                    device = self._get_device()
                    if device and device.get("state"):
                        api_value = device["state"].get(self._parameter_name)
                        if api_value is False or api_value == 0:
                            # État confirmé par l'API, on peut abandonner l'état optimiste
                            _LOGGER.info(f"{self._attr_name} turned off confirmed after {(attempt+1)*POLLING_INTERVAL}s")
                            self._optimistic_state = None
                            self.async_write_ha_state()
                            return
                
                # Après le timeout, abandonner l'état optimiste même sans confirmation
                _LOGGER.warning(f"{self._attr_name} turn off not confirmed after 30s, assuming success")
                self._optimistic_state = None
                self.async_write_ha_state()
            else:
                # En cas d'échec, annuler l'état optimiste
                self._optimistic_state = None
                self.async_write_ha_state()
                _LOGGER.error(f"Failed to turn off {self._attr_name}")
                
        except Exception as err:
            # En cas d'erreur, annuler l'état optimiste
            self._optimistic_state = None
            self.async_write_ha_state()
            _LOGGER.error(f"Error turning off {self._attr_name}: {err}")
    
    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        device = self._get_device()
        if device and device.get("state"):
            state = device["state"]
            attrs = {}
            
            # Ajouter des informations contextuelles selon le switch
            if self._parameter_name == "window":
                attrs["window_timeout_minutes"] = state.get("windowTimeOut")
                attrs["description"] = "Enable/disable automatic open window detection based on temperature drop"
            elif self._parameter_name == "occupancyStatus":
                attrs["description"] = "Enable/disable occupancy consideration for heating control"
            elif self._parameter_name == "selfLearning":
                attrs["self_learning_improve"] = state.get("selfLearningImprove")
                attrs["self_learning_days"] = state.get("selfLearningCountDay")
                attrs["description"] = "Enable/disable auto-learning mode (requires occupancyStatus enabled)"
            elif self._parameter_name == "noprog":
                attrs["description"] = "Manual mode (on) or Auto mode with scheduling (off)"
                
            return attrs
        return {}
