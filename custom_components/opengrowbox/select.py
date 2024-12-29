from homeassistant.components.select import SelectEntity
from homeassistant.helpers.restore_state import RestoreEntity
import logging
from .const import DOMAIN
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

class CustomSelect(SelectEntity):
    """Custom select for multiple hubs."""

    def __init__(self, name, hub_name, coordinator, options=None, initial_value=None):
        """Initialize the custom select."""
        self._name = name
        self.hub_name = hub_name
        self._options = options or []  # Default to an empty list if no options are provided
        self._current_option = initial_value if initial_value in self._options else None
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
    def options(self):
        """Return the list of available options."""
        return self._options

    @property
    def current_option(self):
        """Return the currently selected option."""
        return self._current_option

    async def async_select_option(self, option):
        """Set the selected option asynchronously."""
        if option in self._options:
            self._current_option = option
            self.async_write_ha_state()
            _LOGGER.info(f"Select '{self._name}' changed to '{option}'")
        else:
            _LOGGER.warning(f"Invalid option '{option}' for select '{self._name}'")

    def add_options(self, new_options):
        """Add new options to the select entity."""
        self._options.extend([opt for opt in new_options if opt not in self._options])
        if self._current_option not in self._options and self._options:
            self._current_option = self._options[0]  # Set to the first option if the current one is invalid
        self.async_write_ha_state()
        _LOGGER.info(f"Options for '{self._name}' updated to: {self._options}")


    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        return {"hub_name": self.hub_name}

    @property
    def device_info(self):
        """Return device information to link this entity to a device."""
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": f"Device for {self._name}",
            "model": "Select Device",
            "manufacturer": "OpenGrowBox",
            "suggested_area": self.hub_name,
        }
        
        
class OpenGrowBoxRoomSelector(SelectEntity):
    """A global selector for all Home Assistant rooms."""

    def __init__(self, name, options):
        """Initialize the Room Selector."""
        self._attr_name = name
        self._options = options
        self._attr_current_option = options[0] if options else None
        self._unique_id = f"{DOMAIN}_room_selector"

    @property
    def unique_id(self):
        """Return the unique ID for this entity."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the Room Selector."""
        return self._attr_name

    @property
    def options(self):
        """Return the list of available options."""
        return self._options

    @property
    def current_option(self):
        """Return the currently selected option."""
        return self._attr_current_option

    async def async_select_option(self, option: str):
        """Set a new room as selected."""
        if option in self._options:
            self._attr_current_option = option
            self.async_write_ha_state()  # Sicherstellen, dass dies im Event-Loop läuft
            _LOGGER.info(f"Room Selector changed to: {option}")
        else:
            _LOGGER.warning(f"Invalid room selection: {option}")

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        return {}

    @property
    def device_info(self):
        """Return device information for the Room Selector."""
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": "Room Selector",
            "model": "Room Selector Device",
            "manufacturer": "OpenGrowBox",
        }


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up select entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Add global Room Selector if not already added
    if "room_selector" not in hass.data[DOMAIN]:
        room_selector = coordinator.create_room_selector()
        hass.data[DOMAIN]["room_selector"] = room_selector
        async_add_entities([room_selector])

    # Create hub-specific selects
    selects = [
        CustomSelect(f"OGB_PlantStage_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["Germination", "Clones", "EarlyVeg", "MidVeg", "LateVeg", "EarlyFlower", "MidFlower", "LateFlower",""]),
        CustomSelect(f"OGB_TentMode_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["VPD Perfection", "IN-VPD-Range", "Targeted VPD", "Experimentel","Drying","Disabled",""]),
        CustomSelect(f"OGB_HoldVPDNight_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["YES", "NO",""], initial_value="YES"),
        CustomSelect(f"OGB_ControlSet_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["Tent", "Ambient",""], initial_value="Tent"),
        CustomSelect(f"OGB_AmbientControl_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["YES", "NO",""], initial_value="NO"),
        CustomSelect(f"OGB_AutoWatering_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["YES", "NO",""], initial_value="NO"),
        CustomSelect(f"OGB_OwnWeights_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["YES", "NO",""], initial_value="NO"),
        CustomSelect(f"OGB_CO2_Control_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["YES", "NO",""], initial_value="NO"),
        CustomSelect(f"OGB_LightControl_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["YES", "NO",""], initial_value="NO"),
        CustomSelect(f"OGB_GLS_Control_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["YES", "NO",""], initial_value="NO"),
        CustomSelect(f"OGB_VPDLightControl_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["YES", "NO",""], initial_value="NO"),
        CustomSelect(f"OGB_GLS_PlantType_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["Sativa", "Indica",""]),
        CustomSelect(f"OGB_OwnDeviceSets_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["YES", "NO",""], initial_value="NO"),
        CustomSelect(f"OGB_DryingModes_{coordinator.hub_name}", coordinator.hub_name, coordinator,
                     options=["elClassico", "SharkMouse","dewBased",""]),
    ]

    async_add_entities(selects)
  # Register a service to add options to selects
    async def handle_add_options(call):
        """Service to add options to a select entity."""
        entity_id = call.data.get("entity_id")
        options = call.data.get("options", [])

    
        _LOGGER.info(f"Adding options to '{entity_id}': {options}")

        # Find and update the corresponding select
        for select in selects:
            if select.entity_id == entity_id:
                select.add_options(options)
                return

        _LOGGER.warning(f"Select entity with id '{entity_id}' not found.")

    hass.services.async_register(
        DOMAIN,
        "add_select_options",
        handle_add_options,
        schema=vol.Schema({
            vol.Required("entity_id"): str,
            vol.Required("options"): vol.All([str]),
        }),
    )