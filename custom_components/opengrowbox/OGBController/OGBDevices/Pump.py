from .Device import Device

from .Device import Device
import logging
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

class Pump(Device):
    def __init__(self, deviceName, deviceData, eventManager,dataStore, deviceType,inRoom, hass=None):
        super().__init__(deviceName,deviceData,eventManager,dataStore,deviceType,inRoom,hass)
        self.pumpInterval = 3600  # Mindestintervall zwischen Pumpzyklen (in Sekunden)
        self.pumpDuration = 10  # Pumpdauer in Sekunden
        self.isAutoRun = False  # Automatikmodus
        self.OGBAutoMODE = False  # OpenGrowBox Steuerung
        self.lastPumpTime = None  # Zeitpunkt des letzten Pumpvorgangs
        self.soilMoisture = 0  # Bodenfeuchtigkeit
        self.soilEC = 0  # Elektrische Leitfähigkeit
        self.minSoilMoisture = 25  # Mindestbodenfeuchte
        self.maxSoilEC = 2.5  # Maximaler EC-Wert


        ## Events Register
        self.eventManager.on("Increase Pump", self.increaseAction)
        self.eventManager.on("Reduce Pump", self.reduceAction)

    #Actions Helpers
    
    async def increaseAction(self, data):
        """Erhöht den Duty Cycle."""
        self.log_action("IncreaseAction/TurnOn ")
        
    async def reduceAction(self, data):
        """Reduziert den Duty Cycle."""
        self.log_action("ReduceAction/TurnOff ")

    def log_action(self, action_name):
        """Protokolliert die ausgeführte Aktion."""
        log_message = f"{self.deviceName}"
        _LOGGER.warn(f"{action_name}: {log_message}")
