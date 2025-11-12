"""GoodHome Climate Platform."""
import logging
import asyncio
from typing import Any, Callable

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_ECO,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import POLLING_MAX_ATTEMPTS, POLLING_INTERVAL, DEBOUNCE_DELAY

_LOGGER = logging.getLogger(__name__)

PRESET_MANUAL = "manual"

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the GoodHome climate platform (YAML config)."""
    coordinator = hass.data["goodhome"]["coordinator"]
    api = hass.data["goodhome"]["api"]
    
    devices = coordinator.data
    entities = []
    
    for device in devices:
        entities.append(GoodHomeClimate(coordinator, api, device))
    
    async_add_entities(entities, True)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the GoodHome climate platform (config entry)."""
    coordinator = hass.data["goodhome"][entry.entry_id]["coordinator"]
    api = hass.data["goodhome"][entry.entry_id]["api"]
    
    devices = coordinator.data
    entities = []
    
    for device in devices:
        entities.append(GoodHomeClimate(coordinator, api, device))
    
    async_add_entities(entities, True)

class GoodHomeClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a GoodHome Climate device."""
    
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_preset_modes = [PRESET_COMFORT, PRESET_ECO, PRESET_MANUAL, PRESET_AWAY]
    _attr_min_temp = 7
    _attr_max_temp = 30
    _attr_target_temperature_step = 0.5
    
    def __init__(self, coordinator, api, device):
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device["id"]
        self._attr_name = device["name"]
        self._attr_unique_id = f"goodhome_climate_{device['id']}"
        self._debounce_task = None
        self._pending_temperature = None
        self._pending_hvac_mode = None
        self._pending_preset_mode = None
        
    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {("goodhome", self._device_id)},
            "name": self._attr_name,
            "manufacturer": "GoodHome",
            "model": "Thermostat",
        }
    
    @property
    def available(self):
        """Return True if entity is available."""
        device = self._get_device()
        if device:
            return device.get("connected", False)
        return False
    
    def _get_device(self):
        """Get device from coordinator data."""
        for device in self.coordinator.data:
            if device["id"] == self._device_id:
                return device
        return None
    
    async def _wait_for_confirmation(self, check_function: Callable[[], bool], description: str) -> bool:
        """
        Attendre la confirmation d'un changement avec polling.
        
        Args:
            check_function: Fonction qui retourne True si le changement est confirmé
            description: Description du changement pour les logs
            
        Returns:
            True si confirmé, False si timeout
        """
        for attempt in range(POLLING_MAX_ATTEMPTS):
            await asyncio.sleep(POLLING_INTERVAL)
            await self.coordinator.async_request_refresh()
            
            if check_function():
                _LOGGER.debug(f"{description} confirmed after {attempt + 1} attempts")
                return True
            
            _LOGGER.debug(f"Waiting for {description} confirmation... attempt {attempt + 1}/{POLLING_MAX_ATTEMPTS}")
        
        _LOGGER.warning(f"{description} confirmation timeout after {POLLING_MAX_ATTEMPTS} attempts, assuming success")
        return False
    
    @property
    def current_temperature(self):
        """Return the current temperature."""
        device = self._get_device()
        if device and device.get("state"):
            return device["state"].get("currentTemp")
        return None
    
    @property
    def current_humidity(self):
        """Return the current humidity."""
        device = self._get_device()
        if device and device.get("state"):
            humidity = device["state"].get("humidity")
            if humidity is not None:
                return humidity
        return None
    
    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        # Si une température est en attente, l'afficher immédiatement
        if self._pending_temperature is not None:
            return self._pending_temperature
        
        device = self._get_device()
        if device and device.get("state"):
            return device["state"].get("targetTemp")
        return None
    
    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode."""
        # Si un mode est en attente, l'afficher immédiatement
        if self._pending_hvac_mode is not None:
            return self._pending_hvac_mode
        
        device = self._get_device()
        if device and device.get("state"):
            mode = device["state"].get("targetMode", 1)
            # Mode 3 = anti-gel manuel = OFF
            # Mode 0 = default (provisoire) = considéré comme OFF aussi
            if mode in [0, 3]:
                return HVACMode.OFF
            return HVACMode.HEAT
        return HVACMode.HEAT
    
    @property
    def preset_mode(self):
        """Return the current preset mode."""
        # Si un preset est en attente, l'afficher immédiatement
        if self._pending_preset_mode is not None:
            return self._pending_preset_mode
        
        device = self._get_device()
        if device and device.get("state"):
            mode = device["state"].get("targetMode", 1)
            # Mapping inverse selon ESPHome_GoodHome
            if mode in [9, 60]:  # Forcé confort ou Auto confort
                return PRESET_COMFORT
            elif mode in [10, 61]:  # Forcé éco ou Auto éco
                return PRESET_ECO
            elif mode in [1, 2, 3, 8, 70]:  # Modes manuels
                return PRESET_MANUAL
            elif mode in [5, 12]:  # Absence (longue ou courte)
                return PRESET_AWAY
        return PRESET_MANUAL
    
    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        device = self._get_device()
        if device and device.get("state"):
            state = device["state"]
            
            # Déterminer la plage de température pour couleur
            target_temp = state.get("targetTemp", 20)
            if target_temp <= 12.5:
                temp_range = "cold"  # Bleu
                temp_color = "#2196F3"
            elif target_temp <= 19.5:
                temp_range = "medium"  # Vert
                temp_color = "#4CAF50"
            else:
                temp_range = "hot"  # Rouge/Orange
                temp_color = "#FF5722"
            
            # Déterminer la raison du mode éco
            target_mode = state.get("targetMode", 0)
            eco_reason = None
            if target_mode == 2:
                eco_reason = "manual"  # Éco manuel
            elif target_mode == 30:
                eco_reason = "absence"  # Éco automatique après 20+ min sans présence
            elif target_mode == 61:
                eco_reason = "schedule"  # Éco selon planning auto
            
            return {
                "humidity": state.get("humidity"),
                "window_open": state.get("window", False),
                "occupancy": state.get("occupancyStatus", False),
                "duty_cycle": state.get("dutyCycle"),
                "eco_temperature": state.get("ecoTemp"),
                "comfort_temperature": state.get("comfTemp"),
                "antifreeze_temperature": state.get("antifTemp"),
                "override_temperature": state.get("overrideTemp"),
                "override_time": state.get("overrideTime"),
                "self_learning": state.get("selfLearning"),
                "self_learning_improve": state.get("selfLearningImprove"),
                "self_learning_days": state.get("selfLearningCountDay"),
                "eco_reason": eco_reason,  # Raison du mode éco (manual/absence/schedule)
                "firmware_version": state.get("fwVer"),
                "hardware_version": state.get("HwVer"),
                "code_name": state.get("codeName"),
                "room_name": state.get("roomName"),
                "window_timeout": state.get("windowTimeOut"),
                "fault_system": state.get("faultSystem"),
                "temperature_range": temp_range,
                "temperature_color": temp_color,
            }
        return {}
    
    async def async_set_temperature(self, **kwargs):
        """Set new target temperature with debounce."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            # Annuler la tâche de debounce précédente si elle existe
            if self._debounce_task is not None:
                self._debounce_task.cancel()
            
            # Stocker la température en attente
            self._pending_temperature = temperature
            
            # Mettre à jour l'affichage immédiatement avec la valeur locale
            self.async_write_ha_state()
            
            # Créer une nouvelle tâche de debounce
            self._debounce_task = self.hass.async_create_task(
                self._debounced_set_temperature()
            )
    
    async def _debounced_set_temperature(self):
        """Set temperature after debounce delay."""
        try:
            # Attendre le délai de debounce
            await asyncio.sleep(DEBOUNCE_DELAY)
            
            # Envoyer la requête
            if self._pending_temperature is not None:
                temp_to_set = self._pending_temperature
                _LOGGER.debug(f"Setting temperature to {temp_to_set} after debounce")
                
                await self.hass.async_add_executor_job(
                    self._api.set_temperature, self._device_id, temp_to_set
                )
                
                # Fonction de vérification pour le polling
                def check_temperature():
                    device = self._get_device()
                    if device and device.get("state"):
                        current_target = device["state"].get("targetTemp")
                        # Vérifier avec une tolérance de 0.1°C
                        if current_target is not None and abs(current_target - temp_to_set) < 0.1:
                            return True
                    return False
                
                # Attendre la confirmation avec polling
                await self._wait_for_confirmation(check_temperature, f"Temperature {temp_to_set}°C")
                
                # Nettoyer l'état en attente
                self._pending_temperature = None
                self.async_write_ha_state()
                
        except asyncio.CancelledError:
            # La tâche a été annulée, ne rien faire
            _LOGGER.debug("Temperature set cancelled due to new change")
            pass
    
    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        """Set new target hvac mode."""
        # OFF = mode 3 (anti-gel manuel)
        # HEAT = mode 1 (manuel confort)
        if hvac_mode == HVACMode.OFF:
            mode = 3  # Manuel anti-gel
        else:
            mode = 1  # Manuel confort
        
        # État optimiste : afficher immédiatement le nouveau mode
        self._pending_hvac_mode = hvac_mode
        self.async_write_ha_state()
        
        # Envoyer la commande à l'API
        await self.hass.async_add_executor_job(
            self._api.set_mode, self._device_id, mode
        )
        
        # Fonction de vérification pour le polling
        def check_hvac_mode():
            device = self._get_device()
            if device and device.get("state"):
                return device["state"].get("targetMode") == mode
            return False
        
        # Attendre la confirmation avec polling
        await self._wait_for_confirmation(check_hvac_mode, f"HVAC mode {hvac_mode}")
        
        # Nettoyer l'état en attente
        self._pending_hvac_mode = None
        self.async_write_ha_state()
    
    async def async_set_preset_mode(self, preset_mode: str):
        """Set new preset mode."""
        # Mapping simplifié pour les presets courants
        # Pour un contrôle total, utiliser l'entité select.target_mode
        mode_map = {
            PRESET_COMFORT: 9,   # Forcé confort (retour auto)
            PRESET_ECO: 10,      # Forcé éco (retour auto)
            PRESET_MANUAL: 1,    # Manuel confort
            PRESET_AWAY: 5,      # Absence longue durée
        }
        mode = mode_map.get(preset_mode, 1)
        
        # État optimiste : afficher immédiatement le nouveau preset
        self._pending_preset_mode = preset_mode
        self.async_write_ha_state()
        
        # Envoyer la commande à l'API
        await self.hass.async_add_executor_job(
            self._api.set_mode, self._device_id, mode
        )
        
        # Fonction de vérification pour le polling
        def check_preset_mode():
            device = self._get_device()
            if device and device.get("state"):
                return device["state"].get("targetMode") == mode
            return False
        
        # Attendre la confirmation avec polling
        await self._wait_for_confirmation(check_preset_mode, f"Preset mode {preset_mode}")
        
        # Nettoyer l'état en attente
        self._pending_preset_mode = None
        self.async_write_ha_state()
