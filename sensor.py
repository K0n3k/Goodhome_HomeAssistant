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
                "Temperature",
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
                "Target Temperature",
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
                "Humidity",
                PERCENTAGE,
                SensorDeviceClass.HUMIDITY,
                SensorStateClass.MEASUREMENT,
            )
        )
        # Eco Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "eco_temp",
                "Eco Temperature",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
                None,
            )
        )
        # Comfort Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "comfort_temp",
                "Comfort Temperature",
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
                "Duty Cycle",
                PERCENTAGE,
                SensorDeviceClass.POWER_FACTOR,
                SensorStateClass.MEASUREMENT,
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
                "Temperature",
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
                "Target Temperature",
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
                "Humidity",
                PERCENTAGE,
                SensorDeviceClass.HUMIDITY,
                SensorStateClass.MEASUREMENT,
            )
        )
        # Eco Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "eco_temp",
                "Eco Temperature",
                UnitOfTemperature.CELSIUS,
                SensorDeviceClass.TEMPERATURE,
                None,
            )
        )
        # Comfort Temperature sensor
        entities.append(
            GoodHomeSensor(
                coordinator,
                device,
                "comfort_temp",
                "Comfort Temperature",
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
                "Duty Cycle",
                PERCENTAGE,
                SensorDeviceClass.POWER_FACTOR,
                SensorStateClass.MEASUREMENT,
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
        sensor_name,
        unit,
        device_class,
        state_class,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device["id"]
        self._device_name = device["name"]
        self._sensor_type = sensor_type
        self._attr_name = f"{device['name']} {sensor_name}"
        self._attr_unique_id = f"goodhome_{device['id']}_{sensor_type}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        
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
            elif self._sensor_type == "duty_cycle":
                return state.get("dutyCycle")
        return None
    
    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        device = self._get_device()
        if device and device.get("state"):
            state = device["state"]
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
