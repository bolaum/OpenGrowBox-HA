from homeassistant.components.input_select import InputSelect
from homeassistant.helpers.entity import Entity
import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class CustomInputSelect(Entity):
    """Custom input_select implementation for OpenGrowBox."""

    def __init__(self, name, hub_name, coordinator, options=None, initial_value=None):
        """Initialize the input_select entity."""
        self._name = name
        self.hub_name = hub_name
        self._options = options or []
        self._current_option = initial_value if initial_value in self._options else None
        self.coordinator = coordinator
        self._unique_id = f"{DOMAIN}_{hub_name}_{name.lower().replace(' ', '_')}"

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._current_option

    @property
    def extra_state_attributes(self):
        return {"options": self._options, "hub_name": self.hub_name}

    async def async_select_option(self, option):
        """Set the selected option."""
        if option in self._options:
            self._current_option = option
            self.async_write_ha_state()
            _LOGGER.info(f"{self._name} changed to {option}")
        else:
            _LOGGER.warning(f"Invalid option {option} for {self._name}")

    def add_options(self, new_options):
        """Add new options dynamically."""
        self._options.extend(opt for opt in new_options if opt not in self._options)
        self.async_write_ha_state()
        _LOGGER.info(f"Updated options for {self._name}: {self._options}")

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up specific input_select entities for OpenGrowBox."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Nur die spezifischen Geräte als InputSelect definieren
    input_selects = [
        CustomInputSelect(f"OGB_LightSelect_{coordinator.hub_name}", coordinator.hub_name, coordinator, options=[], initial_value=""),
        CustomInputSelect(f"OGB_ExhaustSelect_{coordinator.hub_name}", coordinator.hub_name, coordinator, options=[], initial_value=""),
        CustomInputSelect(f"OGB_VentsSelect_{coordinator.hub_name}", coordinator.hub_name, coordinator, options=[], initial_value=""),
        CustomInputSelect(f"OGB_HumidifierSelect_{coordinator.hub_name}", coordinator.hub_name, coordinator, options=[], initial_value=""),
        CustomInputSelect(f"OGB_DehumidifierSelect_{coordinator.hub_name}", coordinator.hub_name, coordinator, options=[], initial_value=""),
        CustomInputSelect(f"OGB_HeaterSelect_{coordinator.hub_name}", coordinator.hub_name, coordinator, options=[], initial_value=""),
        CustomInputSelect(f"OGB_CoolerSelect_{coordinator.hub_name}", coordinator.hub_name, coordinator, options=[], initial_value=""),
        CustomInputSelect(f"OGB_ClimateSelect_{coordinator.hub_name}", coordinator.hub_name, coordinator, options=[], initial_value=""),
        CustomInputSelect(f"OGB_CO2Select_{coordinator.hub_name}", coordinator.hub_name, coordinator, options=[], initial_value=""),
    ]

    # Entitäten registrieren
    async_add_entities(input_selects)
