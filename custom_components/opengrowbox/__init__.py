import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from custom_components.opengrowbox.const import DOMAIN
from custom_components.opengrowbox.coordinator import IntegrationCoordinator



_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up integration via UI."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Create the coordinator
    coordinator = IntegrationCoordinator(hass, config_entry)
    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    # Initialize global Room Selector
    await coordinator.update_room_selector()

    # Load all platforms
    for platform in ["sensor", "number", "select", "time","switch","input_select"]:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, ["sensor", "number", "select", "time","switch","input_select"]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok
