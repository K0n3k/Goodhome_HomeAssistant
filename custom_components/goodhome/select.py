"""Support for GoodHome Select entities."""
import logging
import asyncio

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import POLLING_MAX_ATTEMPTS, POLLING_INTERVAL

_LOGGER = logging.getLogger(__name__)

# Mapping des modes targetMode selon ESPHome_GoodHome avec traductions
TARGET_MODES = {
    "Par défaut": 0,           # Provisoire, retour au mode par défaut
    "Manuel Confort": 1,        # Manuel, température confort
    "Manuel Éco": 2,            # Manuel, température éco
    "Manuel Hors-gel": 3,       # Manuel, température anti-gel
    "Absence longue": 5,        # Absence de longue durée (holidayTimeout)
    "Override": 8,              # Manuel override
    "Forcé Confort": 9,         # Forcé confort (retour auto)
    "Forcé Éco": 10,            # Forcé éco (retour auto)
    "Absence courte": 12,       # Absence de courte durée (overrideTime)
    "Éco auto (absence)": 30,   # Éco automatique après détection d'absence (20+ min)
    "Auto Confort": 60,         # Mode auto, période de présence
    "Auto Éco": 61,             # Mode auto, période d'absence
    "Manuel": 70,               # Manuel (mise à jour récente)
}

# Mapping inverse pour la lecture
TARGET_MODES_REVERSE = {v: k for k, v in TARGET_MODES.items()}

# Options présentées à l'utilisateur (dans l'ordre logique d'utilisation)
TARGET_MODE_OPTIONS = [
    "Par défaut",
    "Manuel Confort",
    "Manuel Éco", 
    "Manuel Hors-gel",
    "Manuel",
    "Override",
    "Forcé Confort",
    "Forcé Éco",
    "Éco auto (absence)",
    "Auto Confort",
    "Auto Éco",
    "Absence courte",
    "Absence longue",
]

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the GoodHome select platform (YAML)."""
    if discovery_info is None:
        return
    
    coordinator = discovery_info["coordinator"]
    api = discovery_info["api"]
    
    devices = coordinator.data
    entities = []
    
    for device in devices:
        entities.append(GoodHomeTargetModeSelect(coordinator, api, device))
    
    async_add_entities(entities, True)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the GoodHome select platform (config entry)."""
    coordinator = hass.data["goodhome"][entry.entry_id]["coordinator"]
    api = hass.data["goodhome"][entry.entry_id]["api"]
    
    devices = coordinator.data
    entities = []
    
    for device in devices:
        entities.append(GoodHomeTargetModeSelect(coordinator, api, device))
    
    async_add_entities(entities, True)

class GoodHomeTargetModeSelect(CoordinatorEntity, SelectEntity):
    """Representation of a GoodHome Target Mode Select."""
    
    _attr_icon = "mdi:target"
    _attr_has_entity_name = True
    _attr_translation_key = "target_mode"
    
    def __init__(self, coordinator, api, device):
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device["id"]
        self._device_name = device["name"]
        self._attr_unique_id = f"goodhome_target_mode_{device['id']}"
        self._attr_options = TARGET_MODE_OPTIONS
        self._optimistic_state = None
    
    @property
    def device_info(self):
        """Return device info to link this entity to the same device as climate."""
        return {
            "identifiers": {("goodhome", self._device_id)},
            "name": self._device_name,
            "manufacturer": "GoodHome",
            "model": "Thermostat",
        }
    
    def _get_device(self):
        """Get the device data from coordinator."""
        for device in self.coordinator.data:
            if device["id"] == self._device_id:
                return device
        return None
    
    @property
    def current_option(self):
        """Return the current selected option."""
        # Si on a un état optimiste, l'utiliser
        if self._optimistic_state is not None:
            return self._optimistic_state
        
        # Sinon, lire depuis l'API
        device = self._get_device()
        if device and device.get("state"):
            target_mode = device["state"].get("targetMode")
            if target_mode is not None:
                option = TARGET_MODES_REVERSE.get(target_mode, "Par défaut")
                return option
        return "Par défaut"
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in TARGET_MODES:
            _LOGGER.error(f"Unknown target mode: {option}")
            return
        
        mode_value = TARGET_MODES[option]
        
        # État optimiste : afficher immédiatement le changement dans l'interface
        self._optimistic_state = option
        self.async_write_ha_state()
        
        _LOGGER.debug(f"Setting target mode to {option} (value: {mode_value}) for device {self._device_id}")
        
        # Envoyer la commande à l'API
        success = await self.hass.async_add_executor_job(
            self._api.set_parameter,
            self._device_id,
            "targetMode",
            mode_value
        )
        
        if success:
            # Attendre que le thermostat traite la commande (jusqu'à 40 secondes)
            for attempt in range(POLLING_MAX_ATTEMPTS):
                await asyncio.sleep(POLLING_INTERVAL)
                await self.coordinator.async_request_refresh()
                
                # Vérifier si l'état de l'API correspond à notre commande
                device = self._get_device()
                if device and device.get("state"):
                    api_value = device["state"].get("targetMode")
                    if api_value == mode_value:
                        # État confirmé par l'API
                        _LOGGER.info(f"Target mode {option} confirmed after {(attempt+1)*POLLING_INTERVAL}s")
                        self._optimistic_state = None
                        self.async_write_ha_state()
                        return
            
            # Après le timeout, abandonner l'état optimiste même sans confirmation
            _LOGGER.warning(f"Target mode {option} not confirmed after {POLLING_MAX_ATTEMPTS*POLLING_INTERVAL}s, assuming success")
            self._optimistic_state = None
            self.async_write_ha_state()
        else:
            # Échec de la commande, revenir à l'état précédent
            _LOGGER.error(f"Failed to set target mode to {option}")
            self._optimistic_state = None
            self.async_write_ha_state()
    
    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        device = self._get_device()
        if device and device.get("state"):
            state = device["state"]
            target_mode = state.get("targetMode")
            
            return {
                "target_mode_value": target_mode,
                "target_temp": state.get("targetTemp"),
                "eco_temp": state.get("ecoTemp"),
                "comfort_temp": state.get("comfTemp"),
                "antifreeze_temp": state.get("antifTemp"),
                "override_temp": state.get("overrideTemp"),
                "manual_mode": state.get("noprog"),
                "self_learning": state.get("selfLearning"),
                "occupancy_status": state.get("occupancyStatus"),
            }
        return {}
