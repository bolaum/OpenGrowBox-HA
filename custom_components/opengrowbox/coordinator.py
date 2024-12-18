from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta
import logging
from .select import OpenGrowBoxRoomSelector
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class IntegrationCoordinator(DataUpdateCoordinator):
    """Manage data for multiple hubs and global entities."""

    def __init__(self, hass, config_entry):
        """Initialize the coordinator."""
        self.hass = hass
        self.config_entry = config_entry
        self.hub_name = config_entry.data["hub_name"]
        self.entities = {
            "sensor": [],
            "number": [],
            "switch": [],
            "select": [],
            "time": [],
            "input_select": [],
        }
        self.room_selector = None  # Store the Room Selector instance
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.hub_name}",
            update_interval=timedelta(seconds=1),
        )

    async def update_room_selector(self):
        """Update the Room Selector with current Home Assistant rooms."""
        area_registry = async_get_area_registry(self.hass)
        areas = area_registry.async_list_areas()
        room_names = [area.name for area in areas]

        if self.room_selector:
            # Preserve the current selected room
            current_option = self.room_selector.current_option
            self.room_selector._options = room_names
            if current_option in room_names:
                self.room_selector._attr_current_option = current_option
            else:
                self.room_selector._attr_current_option = room_names[0] if room_names else None
            self.room_selector.async_write_ha_state()
            _LOGGER.info(f"Updated Room Selector with rooms: {room_names} (current: {self.room_selector._attr_current_option})")

    def create_room_selector(self):
        """Create a new global Room Selector."""
        area_registry = async_get_area_registry(self.hass)
        areas = area_registry.async_list_areas()
        room_names = [area.name for area in areas]

        self.room_selector = OpenGrowBoxRoomSelector(
            name="OGB Rooms",
            options=room_names
        )
        return self.room_selector
