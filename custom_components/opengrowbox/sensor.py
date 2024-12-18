from homeassistant.helpers.entity import Entity
import logging
from .const import DOMAIN
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

class CustomSensor(Entity):
    """Custom sensor for multiple hubs with update capability and graph support."""

    def __init__(self, name, hub_name, coordinator, initial_value=None, device_class=None):
        """Initialize the sensor."""
        self._name = name
        self._state = initial_value  # Initial value
        self.hub_name = hub_name
        self.coordinator = coordinator
        self._device_class = device_class  # e.g., temperature, humidity, light
        self._unique_id = f"{DOMAIN}_{hub_name}_{name.lower().replace(' ', '_')}"

    @property
    def unique_id(self):
        """Return the unique ID for this entity."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def state(self):
        """Return the current state of the entity."""
        return self._state

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return "measurement"

    @property
    def device_info(self):
        """Return device information to link this entity to a device."""
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": f"Device for {self._name}",
            "model": "Sensor Device",
            "manufacturer": "OpenGrowBox",
            "suggested_area": self.hub_name,
        }


    @property
    def unit_of_measurement(self):
        """Return the unit of measurement for this sensor."""
        if self._device_class == "temperature":
            return "°C"
        elif self._device_class == "humidity":
            return "%"
        elif self._device_class == "pressure":
            return "hPa"
        elif self._device_class == "co2":
            return "ppm"
        elif self._device_class == "vpd":
            return "kPa"
        elif self._device_class == "moisture":
            return "%"
        elif self._device_class == "light":
            return "lx"
        elif self._device_class == "power":
            return "W"
        elif self._device_class == "ppfd":
            return "μmol/m²/s"
        elif self._device_class == "dli":
            return "mol/m²/day"
        elif self._device_class == "battery":
            return "%"
        return None

    @property
    def extra_state_attributes(self):
        """Return extra attributes for the entity."""
        return {"hub_name": self.hub_name}

    def update_state(self, new_state):
        """Update the state and notify Home Assistant."""
        self._state = new_state
        self.async_write_ha_state()
        _LOGGER.info(f"Sensor '{self._name}' updated to state: {new_state}")


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensor entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Create all sensors in a single array
    sensors = [
        # VPD Sensors
        CustomSensor(f"{coordinator.hub_name}_CurrentVPD", coordinator.hub_name, coordinator, initial_value=0.0, device_class="vpd"),
        CustomSensor(f"{coordinator.hub_name}_AVGTemperature", coordinator.hub_name, coordinator, initial_value=0.0, device_class="temperature"),
        CustomSensor(f"{coordinator.hub_name}_AVGDewpoint", coordinator.hub_name, coordinator, initial_value=0.0, device_class="temperature"),
        CustomSensor(f"{coordinator.hub_name}_AVGHumidity", coordinator.hub_name, coordinator, initial_value=0.0, device_class="humidity"),

        # Ambient Sensors
        CustomSensor(f"{coordinator.hub_name}_AmbientTemperature", coordinator.hub_name, coordinator, initial_value=0.0, device_class="temperature"),
        CustomSensor(f"{coordinator.hub_name}_AmbientDewpoint", coordinator.hub_name, coordinator, initial_value=0.0, device_class="temperature"),
        CustomSensor(f"{coordinator.hub_name}_AmbientHumidity", coordinator.hub_name, coordinator, initial_value=0.0, device_class="humidity"),
        CustomSensor(f"{coordinator.hub_name}_AmbientVPD", coordinator.hub_name, coordinator, initial_value=0.0, device_class="vpd"),

        # Outside Sensors
        CustomSensor(f"{coordinator.hub_name}_OutsiteTemperature", coordinator.hub_name, coordinator, initial_value=0.0, device_class="temperature"),
        CustomSensor(f"{coordinator.hub_name}_OutsiteDewpoint", coordinator.hub_name, coordinator, initial_value=0.0, device_class="temperature"),
        CustomSensor(f"{coordinator.hub_name}_OutsiteHumidity", coordinator.hub_name, coordinator, initial_value=0.0, device_class="humidity"),

        # Soil Sensors
        CustomSensor(f"{coordinator.hub_name}_SoilMoisture", coordinator.hub_name, coordinator, initial_value=0.0, device_class="moisture"),
        CustomSensor(f"{coordinator.hub_name}_SoilEC", coordinator.hub_name, coordinator, initial_value=0.0, device_class="moisture"),
        CustomSensor(f"{coordinator.hub_name}_RootTemp", coordinator.hub_name, coordinator, initial_value=0.0, device_class="temperature"),
        
        # Light Sensors
        CustomSensor(f"{coordinator.hub_name}_LightIntensity", coordinator.hub_name, coordinator, initial_value=0.0, device_class="light"),
        CustomSensor(f"{coordinator.hub_name}_LightPower", coordinator.hub_name, coordinator, initial_value=0.0, device_class="power"),
        CustomSensor(f"{coordinator.hub_name}_PPFD", coordinator.hub_name, coordinator, initial_value=0.0, device_class="ppfd"),
        CustomSensor(f"{coordinator.hub_name}_DLI", coordinator.hub_name, coordinator, initial_value=0.0, device_class="dli"),

        # CO2 and Pressure Sensors
        CustomSensor(f"{coordinator.hub_name}_CO2", coordinator.hub_name, coordinator, initial_value=400.0, device_class="co2"),
        CustomSensor(f"{coordinator.hub_name}_Pressure", coordinator.hub_name, coordinator, initial_value=950.0, device_class="pressure"),
    ]

    # Register the sensors globally in hass.data
    if "sensors" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["sensors"] = []

    hass.data[DOMAIN]["sensors"].extend(sensors)

    # Add entities to Home Assistant
    async_add_entities(sensors)

    # Register a global service for updating sensor states if not already registered
    if not hass.services.has_service(DOMAIN, "update_sensor"):
        async def handle_update_sensor(call):
            """Handle the update sensor service."""
            entity_id = call.data.get("entity_id")
            value = call.data.get("value")

            _LOGGER.info(f"Received request to update sensor '{entity_id}' with value: {value}")

            # Find and update the corresponding sensor
            for sensor in hass.data[DOMAIN]["sensors"]:
                if sensor.entity_id == entity_id:
                    sensor.update_state(value)
                    _LOGGER.info(f"Updated sensor '{sensor.name}' to value: {value}")
                    return

            _LOGGER.warning(f"Sensor with entity_id '{entity_id}' not found.")

        # Register the service in Home Assistant
        hass.services.async_register(
            DOMAIN,
            "update_sensor",
            handle_update_sensor,
            schema=vol.Schema({
                vol.Required("entity_id"): str,
                vol.Required("value"): vol.Any(float, int, str),
            }),
        )
