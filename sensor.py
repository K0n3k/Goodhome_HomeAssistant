"""GoodHome Sensor Platform."""
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the GoodHome sensor platform (YAML config)."""
    coordinator = hass.data["goodhome"]["coordinator"]
    
    devices = coordinator.data
    entities = []
    
    for device in devices:
        # Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "temperature",
                "current_temp",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
                SensorStateClass.MEASUREMENT,
            )
        )
        # Target Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "target_temperature",
                "target_temp",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
                SensorStateClass.MEASUREMENT,
            )
        )
        # Humidity sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "humidity",
                "humidity",
                PERCENTAGE,
                SensorDeviceClass.HUMIDITY,
                SensorStateClass.MEASUREMENT,
            )
        )
        # Comfort Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "comfort_temp",
                "comfort_temp",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
                None,
            )
        )
        # Eco Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "eco_temp",
                "eco_temp",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
                None,
            )
        )
        # Antifreeze Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "antifreeze_temp",
                "antifreeze_temp",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
                None,
            )
        )
        # Duty Cycle sensor (heating power)
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "duty_cycle",
                "duty_cycle",
                PERCENTAGE,
                SensorDeviceClass.POWER_FACTOR,
                SensorStateClass.MEASUREMENT,
            )
        )
        # Power consumption sensor (calculated from duty_cycle and device power)
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "power_consumption",
                "power_consumption",
                "W",
                SensorDeviceClass.POWER,
                SensorStateClass.MEASUREMENT,
            )
        )
        # Device Info sensor (diagnostic)
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "device_info",
                "device_info",
                None,
                None,
                None,
                EntityCategory.DIAGNOSTIC,
            )
        )

        # Auto-learning progress sensor (14-day learning period)
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "self_learning_days",
                "self_learning_days",
                "d",
                None,
                None,
            )
        )
    
    async_add_entities(entities, True)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the GoodHome sensor platform (config entry)."""
    coordinator = hass.data["goodhome"][entry.entry_id]["coordinator"]
    
    devices = coordinator.data
    entities = []
    
    for device in devices:
        # Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "temperature",
                "current_temp",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
                SensorStateClass.MEASUREMENT,
            )
        )
        # Target Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "target_temperature",
                "target_temp",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
                SensorStateClass.MEASUREMENT,
            )
        )
        # Humidity sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "humidity",
                "humidity",
                PERCENTAGE,
                SensorDeviceClass.HUMIDITY,
                SensorStateClass.MEASUREMENT,
            )
        )
        # Comfort Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "comfort_temp",
                "comfort_temp",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
                None,
            )
        )
        # Eco Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "eco_temp",
                "eco_temp",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
                None,
            )
        )
        # Antifreeze Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "antifreeze_temp",
                "antifreeze_temp",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
                None,
            )
        )
        # Duty Cycle sensor (heating power)
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "duty_cycle",
                "duty_cycle",
                PERCENTAGE,
                SensorDeviceClass.POWER_FACTOR,
                SensorStateClass.MEASUREMENT,
            )
        )
        # Power consumption sensor (calculated from duty_cycle and device power)
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "power_consumption",
                "power_consumption",
                "W",
                SensorDeviceClass.POWER,
                SensorStateClass.MEASUREMENT,
            )
        )
        # Device Info sensor (diagnostic)
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "device_info",
                "device_info",
                None,
                None,
                None,
                EntityCategory.DIAGNOSTIC,
            )
        )

        # Auto-learning progress sensor (14-day learning period)
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "self_learning_days",
                "self_learning_days",
                "d",
                None,
                None,
            )
        )
    
    async_add_entities(entities, True)

class GoodHomeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a GoodHome Sensor."""
    
    def __init__(
        self,
        coordinator,
        device,
        sensor_type,
        translation_key,
        unit,
        device_class,
        state_class,
        entity_category=None,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device["id"]
        self._device_name = device["name"]
        self._sensor_type = sensor_type
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._attr_unique_id = f"goodhome_{device['id']}_{sensor_type}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_entity_category = entity_category
        
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
        """Return the state of the sensor."""
        device = self._get_device()
        if device and device.get("state"):
            state = device["state"]
            if self._sensor_type == "temperature":
                return state.get("currentTemp")
            elif self._sensor_type == "target_temperature":
                return state.get("targetTemp")
            elif self._sensor_type == "humidity":
                return state.get("humidity")
            elif self._sensor_type == "eco_temp":
                return state.get("ecoTemp")
            elif self._sensor_type == "comfort_temp":
                return state.get("comfTemp")
            elif self._sensor_type == "antifreeze_temp":
                return state.get("antifTemp")
            elif self._sensor_type == "duty_cycle":
                return state.get("dutyCycle")
            elif self._sensor_type == "power_consumption":
                # Calculer la consommation : duty_cycle (%) * puissance nominale (W)
                duty_cycle = state.get("dutyCycle", 0)
                code_name = state.get("codeName", "")
                
                # Extraire la puissance du codeName (ex: "DLRIRFH1800" -> 1800W)
                power_watts = None
                if code_name:
                    try:
                        import re
                        # Extract trailing numeric digits (e.g., 1800 from DLRIRFH1800)
                        match = re.search(r'(\d+)$', code_name)
                        if match:
                            power_watts = int(match.group(1))
                    except (ValueError, AttributeError):
                        pass
                
                # Si on a la puissance et le duty cycle, calculer la consommation
                if power_watts is not None and duty_cycle is not None:
                    # duty_cycle est en %, donc diviser par 100
                    return round((duty_cycle / 100.0) * power_watts, 1)
                return 0
            elif self._sensor_type == "device_info":
                # Retourner un résumé textuel
                fw_ver = state.get("fwVer", "Unknown")
                hw_ver = state.get("HwVer", "Unknown")
                return f"FW: {fw_ver} | HW: {hw_ver}"
            elif self._sensor_type == "self_learning_days":
                # Auto-learning day counter (14-day learning period)
                return state.get("selfLearningCountDay")
        return None
    
    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        device = self._get_device()
        if device and device.get("state"):
            state = device["state"]
            
            # Attributs spécifiques pour device_info sensor
            if self._sensor_type == "device_info":
                # Extraire la puissance du codeName (ex: "DLRIRFH1800" -> 1800W)
                code_name = state.get("codeName", "")
                power_watts = None
                if code_name:
                    try:
                        import re
                        # Extract trailing numeric digits (e.g., 1800 from DLRIRFH1800)
                        match = re.search(r'(\d+)$', code_name)
                        if match:
                            power_watts = int(match.group(1))
                    except (ValueError, AttributeError):
                        pass
                
                attrs = {
                    "device_type": device.get("type"),
                    "power_watts": power_watts,
                    "firmware_version": state.get("fwVer"),
                    "hardware_version": state.get("HwVer"),
                    "code_name": code_name,
                    "room_name": state.get("roomName"),
                    "fault_system": state.get("faultSystem"),
                    "window_timeout": state.get("windowTimeOut"),
                    "override_time": state.get("overrideTime"),
                    "self_learning_days": state.get("selfLearningCountDay"),
                    "connected": device.get("connected", False),
                    "device_id": self._device_id,
                }
                return attrs
            
            # Attributs généraux pour les autres sensors
            return {
                "firmware_version": state.get("fwVer"),
                "hardware_version": state.get("HwVer"),
                "code_name": state.get("codeName"),
                "room_name": state.get("roomName"),
                "self_learning": state.get("selfLearning"),
                "self_learning_improve": state.get("selfLearningImprove"),
                "self_learning_days": state.get("selfLearningCountDay"),
                "antifreeze_temp": state.get("antifTemp"),
                "override_temp": state.get("overrideTemp"),
                "override_time": state.get("overrideTime"),
                "window_timeout": state.get("windowTimeOut"),
                "fault_system": state.get("faultSystem"),
            }
        return {}
