from .Device import Device

from .Device import Device
import logging

_LOGGER = logging.getLogger(__name__)

class Climate(Device):
    def __init__(self, deviceName, deviceData, eventManager, dataStore, deviceType, inRoom, hass=None):
        super().__init__(deviceName, deviceData, eventManager, dataStore, deviceType, inRoom, hass)
        self.currentHAVOC = "off"
        self.havocs = {
            "dry": "dry",  # Entfeuchten
            "cool": "cool",  # Kühlen
            "off": "off",   # Aus
        }
        self.isRunning = False

        # Events Register
        self.eventManager.on("Increase Climate", self.increaseAction)
        self.eventManager.on("Reduce Climate", self.reduceAction)
        self.eventManager.on("Eval Climate", self.evalAction)

    async def evalAction(self, data):
        """
        Evaluates and selects the necessary mode based on VPD control and capabilities.
        """
        self.log_action("Eval Needed Action")
        roomCapabilities = self.dataStore.get("capabilities")

        action = data.get("action", "unknown")  # `increase` or `reduce`
        _LOGGER.warn(f"EvalAction: Action={action}, RoomCapabilities={roomCapabilities}")

        if action == "reduce":
            await self.handleReduce(roomCapabilities)
        elif action == "increase":
            await self.handleIncrease(roomCapabilities)
        else:
            _LOGGER.error(f"Unknown action received: {action}")

    async def handleReduce(self, capabilities):
        """
        Handles the reduce action: Selects 'cool' if available.
        """
        self.log_action("Handle Reduce Action")

        # Reduktion nur durch Kühlung
        if capabilities.get("canCool", {}).get("state") and self.currentHAVOC != "cool":
            self.activateMode("cool")
        else:
            _LOGGER.warn(f"No suitable modes available for reduce action in {self.deviceName}.")

    async def handleIncrease(self, capabilities):
        """
        Handles the increase action: Selects 'dry' if available.
        """
        self.log_action("Handle Increase Action")

        # Erhöhung nur durch Entfeuchtung
        if capabilities.get("canDehumidify", {}).get("state") and self.currentHAVOC != "dry":
            self.activateMode("dry")
        else:
            _LOGGER.warn(f"No suitable modes available for increase action in {self.deviceName}.")

    def activateMode(self, mode):
        """
        Activates the specified mode on the device.
        """
        self.currentHAVOC = mode
        self.isRunning = mode != "off"
        _LOGGER.warn(f"{self.deviceName} Activating mode: {mode}")

    async def increaseAction(self, data):
        """Handles Increase action."""
        self.log_action("Increase Action / Turn On")
        await self.evalAction({"action": "increase"})

    async def reduceAction(self, data):
        """Handles Reduce action."""
        self.log_action("Reduce Action / Turn Off")
        await self.evalAction({"action": "reduce"})

    def log_action(self, action_name):
        """Logs the performed action."""
        log_message = f"{self.deviceName} CurrentHAVOC: {self.currentHAVOC}"
        _LOGGER.warn(f"{action_name}: {log_message}")
