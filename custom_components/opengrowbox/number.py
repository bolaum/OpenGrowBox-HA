from homeassistant.components.number import NumberEntity
from homeassistant.helpers.restore_state import RestoreEntity
import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class CustomNumber(NumberEntity,RestoreEntity):
    """Custom number entity for multiple hubs."""

    def __init__(self, name, hub_name, coordinator, min_value, max_value, step, unit, initial_value=None):
        """Initialize the number entity."""
        self._name = name
        self.hub_name = hub_name
        self._min_value = min_value
        self._max_value = max_value
        self._step = step
        self._unit = unit
        self._value = initial_value or min_value
        self.coordinator = coordinator
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
    def native_min_value(self):
        return self._min_value

    @property
    def native_max_value(self):
        return self._max_value

    @property
    def native_step(self):
        return self._step

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def native_value(self):
        """Return the current value of the number."""
        return self._value

    @property
    def device_info(self):
        """Return device information to link this entity to a device."""
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": f"Device for {self._name}",
            "model": "Number Device",
            "manufacturer": "OpenGrowBox",
            "suggested_area": self.hub_name,  # Optional: Gibt einen Hinweis für den Bereich
        }
        
    async def async_added_to_hass(self):
        """Restore last known state on startup."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state is not None:
            try:
                # Stelle den Wert nur wieder her, wenn er innerhalb des zulässigen Bereichs liegt
                restored_value = float(last_state.state)
                if self._min_value <= restored_value <= self._max_value:
                    self._value = restored_value
                    _LOGGER.info(f"Restored value for '{self._name}': {restored_value}")
                else:
                    _LOGGER.warning(f"Restored value for '{self._name}' out of range: {restored_value}")
            except ValueError:
                _LOGGER.warning(f"Invalid restored value for '{self._name}': {last_state.state}")

    async def async_set_native_value(self, value: float):
        """Set a new value."""
        if self._min_value <= value <= self._max_value:
            self._value = value
            self.async_write_ha_state()
            _LOGGER.info(f"Number '{self._name}' set to {value}")
        else:
            _LOGGER.warning(f"Value {value} out of range for '{self._name}'")

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up number entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Create number entities
    numbers = [
        CustomNumber(f"OGB_LeafTemp_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                min_value=0.0, max_value=5.0, step=0.1, unit="°C", initial_value=2.0),
        CustomNumber(f"OGB_VPDTarget_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                    min_value=0.0, max_value=5.0, step=0.1, unit="°C", initial_value=0.0),
      
        CustomNumber(f"OGB_TemperatureWeight_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=00.0, max_value=2.0, step=0.1, unit="X", initial_value=1.0),
        CustomNumber(f"OGB_HumidityWeight_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=2.0, step=0.1, unit="X", initial_value=1.0),
        
        ##PUMP
        CustomNumber(f"OGB_PumpIntervall_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=24, step=0.1, unit="Hours", initial_value=0),
        CustomNumber(f"OGB_Waterduration_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=600, step=1, unit="Seconds", initial_value=0),
        
        
        ##CO2
        CustomNumber(f"OGB_CO2MinValue_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=2000, step=5, unit="ppm", initial_value=400),
        CustomNumber(f"OGB_CO2MaxValue_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=2000, step=5, unit="ppm", initial_value=400),
        CustomNumber(f"OGB_CO2TargetValue_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=2000, step=5, unit="ppm", initial_value=400),
        
        ##PID VPD
        CustomNumber(f"OGB_ProportionalVPDFaktor_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=100, step=0.1, unit="P", initial_value=1.0),
        CustomNumber(f"OGB_IntegralVPDFaktor_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=1, step=0.1, unit="I", initial_value=0.01),
        CustomNumber(f"OGB_DerivativVPDFaktor_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=10, step=0.1, unit="D", initial_value=0.1),
        #PID TEMP
        CustomNumber(f"OGB_ProportionalTempFaktor_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=100, step=0.1, unit="P", initial_value=1.0),
        CustomNumber(f"OGB_IntegralTempFaktor_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=1, step=0.1, unit="I", initial_value=0.01),
        CustomNumber(f"OGB_DerivativTempFaktor_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=10, step=0.1, unit="D", initial_value=0.1),
        #PID Hum
        CustomNumber(f"OGB_ProportionalHumFaktor_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=100, step=0.1, unit="P", initial_value=1.0),
        CustomNumber(f"OGB_IntegralHumFaktor_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=1, step=0.1, unit="I", initial_value=0.01),
        CustomNumber(f"OGB_DerivativHumFaktor_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     min_value=0.0, max_value=10, step=0.1, unit="D", initial_value=0.1),       
    ]

    if "numbers" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["numbers"] = []

    hass.data[DOMAIN]["numbers"].extend(numbers)
    async_add_entities(numbers)
