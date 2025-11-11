"""GoodHome Binary Sensor Platform."""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the GoodHome binary sensor platform (YAML config)."""
    coordinator = hass.data["goodhome"]["coordinator"]
    
    devices = coordinator.data
    entities = []
    
    for device in devices:
        # Connectivity sensor
        entities.append(
            GoodHomeBinarySensor(
                coordinator,
                device,
                "connectivity",
                "Connectivity",
                BinarySensorDeviceClass.CONNECTIVITY,
            )
        )
        # Self Learning Improve sensor (read-only status)
        entities.append(
            GoodHomeBinarySensor(
                coordinator,
                device,
                "self_learning_improve",
                "Self Learning Improve",
                None,
            )
        )
        # Problem sensor (fault system)
        entities.append(
            GoodHomeBinarySensor(
                coordinator,
                device,
                "problem",
                "Problem",
                BinarySensorDeviceClass.PROBLEM,
            )
        )
    
    async_add_entities(entities, True)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the GoodHome binary sensor platform (config entry)."""
    coordinator = hass.data["goodhome"][entry.entry_id]["coordinator"]
    
    devices = coordinator.data
    entities = []
    
    for device in devices:
        # Connectivity sensor
        entities.append(
            GoodHomeBinarySensor(
                coordinator,
                device,
                "connectivity",
                "Connectivity",
                BinarySensorDeviceClass.CONNECTIVITY,
            )
        )
        # Self Learning Improve sensor (read-only status)
        entities.append(
            GoodHomeBinarySensor(
                coordinator,
                device,
                "self_learning_improve",
                "Self Learning Improve",
                None,
            )
        )
        # Problem sensor (fault system)
        entities.append(
            GoodHomeBinarySensor(
                coordinator,
                device,
                "problem",
                "Problem",
                BinarySensorDeviceClass.PROBLEM,
            )
        )
    
    async_add_entities(entities, True)

class GoodHomeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a GoodHome Binary Sensor."""
    
    def __init__(self, coordinator, device, sensor_type, sensor_name, device_class):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._device_id = device["id"]
        self._device_name = device["name"]
        self._sensor_type = sensor_type
        self._attr_name = f"{device['name']} {sensor_name}"
        self._attr_unique_id = f"goodhome_{device['id']}_{sensor_type}"
        self._attr_device_class = device_class
        
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
        if self._sensor_type == "connectivity":
            return True
        device = self._get_device()
        if device:
            return device.get("connected", False)
        return False
    
    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        device = self._get_device()
        if device:
            if self._sensor_type == "connectivity":
                return device.get("connected", False)
            elif self._sensor_type == "self_learning_improve":
                if device.get("state"):
                    return device["state"].get("selfLearningImprove", False)
            elif self._sensor_type == "problem":
                if device.get("state"):
                    fault = device["state"].get("faultSystem", 0)
                    return fault != 0
        return False
    
    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        device = self._get_device()
        if device and device.get("state"):
            state = device["state"]
            attrs = {}
            
            if self._sensor_type == "self_learning_improve":
                attrs["self_learning_days"] = state.get("selfLearningCountDay")
                attrs["self_learning_enabled"] = state.get("selfLearning", False)
            elif self._sensor_type == "problem":
                attrs["fault_code"] = state.get("faultSystem")
                
            return attrs
        return {}
