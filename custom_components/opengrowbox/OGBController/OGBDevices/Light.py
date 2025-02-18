from .Device import Device
import logging
from datetime import datetime
import asyncio

_LOGGER = logging.getLogger(__name__)

class Light(Device):
    def __init__(self, deviceName, deviceData, eventManager,dataStore, deviceType,inRoom, hass=None):
        super().__init__(deviceName,deviceData,eventManager,dataStore,deviceType,inRoom,hass)
        self.voltage = 0
        self.minVoltage = 20
        self.maxVoltage = 100
        self.steps = 1
        
        
        # Light Times
        self.islightON = None
        self.ogbLightControl = None
        
        self.lightOnTime =  ""
        self.lightOffTime =  ""
        self.sunRiseTime =  ""
        self.sunSetTime = ""
        self.isScheduled = False

        # Sunrise/Sunset
        self.sunPhases = {
            "sunRise": {
                "isSunRise": False,
                "isRunning": False,
                "time": "",
                "minSunRise": 20,
                "maxSunRise": self.maxVoltage,
            },
            "sunSet": {
                "isSunSet": False,
                "isRunning": False,
                "time": "",
                "minSunSet": 20,
                "maxSunSet": self.maxVoltage,
                "startDuty": None,
            },
        }
        
        # Plant Phase
        self.currentPlantStage = ""
        self.currentMinMax= {"min":0,"max":0}
        self.PlantStageMinMax = {
            "Germ": {"min": 20, "max": 30},
            "Veg": {"min": 30, "max": 55},
            "Flower": {"min": 70, "max": 100},
        }

        self.init()
        
        # SunPhaseListener
        asyncio.create_task(self.periodic_sun_phase_check())
        
        ## Events Register
        self.eventManager.on("SunRiseTimeUpdates", self.updateSunRiseTime)   
        self.eventManager.on("SunSetTimeUpdates", self.updateSunSetTime)
        self.eventManager.on("PlantStageChange", self.setPlanStageLight)
        
        self.eventManager.on("toggleLight", self.toggleLight)
        self.eventManager.on("Increase Light", self.increaseAction)
        self.eventManager.on("Reduce Light", self.reduceAction)



    def __repr__(self):
        return (f"DeviceName:'{self.deviceName}' Typ:'{self.deviceType}'RunningState:'{self.isRunning}'"
                f"Dimmable:'{self.isDimmable}' Switches:'{self.switches}' Sensors:'{self.sensors}'"
                f"Options:'{self.options}' OGBS:'{self.ogbsettings}' islightON: '{self.islightON}'"
                f"StartTime:'{self.lightOnTime}' StopTime:{self.lightOffTime} SunRiseTime:'{self.sunRiseTime}' SunSetTime:'{self.sunSetTime}'"
                ) 
        
    def init(self):
        self.setLightTimes()
        
    def initVoltage():
        return NotImplemented
        
    def setLightTimes(self):
        dataStoreTest = self.dataStore
        _LOGGER.debug(f"{self.deviceName}: DataStoreTest  {dataStoreTest}")
        self.lightOnTime = self.dataStore.getDeep("isPlantDay.lightOnTime")
        self.lightOffTime = self.dataStore.getDeep("isPlantDay.lightOffTime")
        self.sunRiseTime = self.dataStore.getDeep("isPlantDay.sunRiseTime")
        self.sunSetTime = self.dataStore.getDeep("isPlantDay.sunSetTime")
        self.islightON = self.dataStore.getDeep("isPlantDay.islightON")
        _LOGGER.debug(f"{self.deviceName}: LightTime-Setup LightOn:{self.islightON} Start:{self.lightOnTime} Stop:{self.lightOffTime} SunRise:{self.sunRiseTime} SunSet:{self.sunSetTime}")               

    ## Helpers
    def voltageFactor(self):
        """Berechnet den Faktor zur Umrechnung des Duty-Cycles in die tatsächliche Spannung."""
        max_device_voltage = 10  # Maximale Gerätespannung, z. B. 10 V
        return max_device_voltage / 100  # Faktor, um 0-100% auf 0-10 V zu skalieren

    def calculate_actual_voltage(self, voltage):
        """Berechnet die tatsächliche Spannung basierend auf einem Duty-Cycle (0-100%)."""
        return voltage * self.voltageFactor()

    def clamp_voltage(self, voltage):
        """Begrenzt den Duty-Cycle auf erlaubte Werte."""
        clamped_value = max(self.minVoltage, min(self.maxVoltage, voltage))
        _LOGGER.debug(f"{self.deviceName}: Duty Cycle auf {clamped_value}% begrenzt.")
        return clamped_value

    def setPlanStageLight(self, plantStage):
        if self.isDimmable == False: return None
        self.currentPlantStage = plantStage
        if plantStage in self.PlantStageMinMax:
            self.currentMinMax = self.PlantStageMinMax[plantStage]
        else:
            _LOGGER.warning(f"{self.deviceName}: Unbekannte Pflanzenphase '{plantStage}'. Standardwerte werden verwendet.")
            self.currentMinMax = {"min": self.minVoltage, "max": self.maxVoltage}


    #Actions Helpers
    def change_voltage(self, increase=True):
        """
        Ändert die Spannung basierend auf dem Schrittwert.
        Erhöht oder verringert die Spannung und begrenzt den Wert mit clamp.
        """
        if not self.isDimmable:
            _LOGGER.warning(f"{self.deviceName}: Änderung an Voltage nicht möglich, da Gerät nicht dimmbar ist.")
            return None
        
        # Berechne neuen Duty-Cycle basierend auf Schrittweite
        new_voltage = self.voltage + self.steps if increase else self.voltage - self.steps
        # Begrenze den neuen Duty-Cycle
        clamped_voltage = self.clamp_voltage(new_voltage)
        self.voltage = clamped_voltage
        
        # Berechne die tatsächliche Spannung
        actual_voltage = self.calculate_actual_voltage(self.voltage)
        _LOGGER.info(f"{self.deviceName}: Voltage geändert auf {self.voltage}% (Actual Voltage: {actual_voltage:.2f} V)")
        return actual_voltage

    #SunPhases Helpers
    def parse_time(self, time_str):
        # Erwartet "HH:MM" als Format – ggf. erweitern, wenn auch Sekunden mitkommen
        if time_str:
            hrs, mins = map(int, time_str.split(":"))
            return time(hrs, mins)
        return None
 
    def updateSunRiseTime(self,time):
        if self.isDimmable == False : return None
        self.sunRiseTime = self.parse_time(time)
        
    def updateSunSetTime(self,time):
        if self.isDimmable == False : return None
        self.sunSetTime = self.parse_time(time)

 
    def checkSunPhase(self):
        if self.isDimmable == False: return None
        sunRiseTime = self.dataStore.getDeep("isPlantDay.sunRiseTime")
        sunSetTime = self.dataStore.getDeep("isPlantDay.sunSetTime")
        
        if sunRiseTime  == "00:00":
            _LOGGER.warn(f"{self.deviceName}: SunRisePhase Value Indicates no SunPhase Set")
            return None 
        
        if sunSetTime == "00:00":
            _LOGGER.warn(f"{self.deviceName}: SunSetPhase Value Indicates no SunPhase Set")
            return None 
        
        
        def checkSunRise(sunRiseTime):
            
            pass
        
        def checkSunSet(sunSetTime):
            pass

    async def periodic_sun_phase_check(self):
        """Überprüft periodisch (z. B. jede Minute) ob die Sonnenphase (Auf- oder Untergang) starten soll."""
        if self.isDimmable == False: return None
        while True:
            now = datetime.now().time()
            # Prüfe, ob es in den "Sunrise-Fenster" fällt (z. B. 10 Minuten vor bis 5 Minuten nach dem eingestellten Sonnenaufgang)
            if self.sunRiseTime and self.within_window(now, self.sunRiseTime, pre=5, post=0) and not self.sunrise_phase_active:
                self.log_action("Starte Sunrise Phase")
                self.sunrise_phase_active = True
                await self.start_sunrise_phase()
            # Prüfe, ob es in den "Sunset-Fenster" fällt (z. B. 5 Minuten vor Lichtaus, also Sonnenuntergang)
            elif self.sunSetTime and self.within_window(now, self.sunSetTime, pre=5, post=0) and not self.sunset_phase_active:
                self.log_action("Starte Sunset Phase")
                self.sunset_phase_active = True
                await self.start_sunset_phase()
            # Hier könnte man auch Logik einbauen, um den Phase-Status zurückzusetzen, wenn die Phase beendet ist.
            await asyncio.sleep(60)  # Check alle 60 Sekunden
     
    # SunPhases
    def within_window(self, current, target, pre=0, post=0):
        """
        Überprüft, ob die aktuelle Zeit innerhalb eines Fensters liegt, das vor (pre) bzw. nach (post) der Zielzeit liegt.
        Die Zeiten werden als datetime.time erwartet, Fensterangaben in Minuten.
        """
        # Umrechnung in Minuten seit Mitternacht:
        current_minutes = current.hour * 60 + current.minute
        target_minutes = target.hour * 60 + target.minute
        return (target_minutes - pre) <= current_minutes <= (target_minutes + post)

    async def start_sunrise_phase(self):
        """Führt die Logik des Sonnenaufgangs aus (z. B. allmähliches Hochfahren der Helligkeit)."""
        # Beispiel: Erhöhe die Helligkeit in kleinen Schritten
        for step in range(10):
            # Berechne neue Spannung oder Duty Cycle
            new_voltage = self.calculate_voltage_for_sunrise(step)
            await self.turn_on(brightness_pct=new_voltage)
            await asyncio.sleep(30)  # Warte 30 Sekunden zwischen den Schritten
        # Nach Abschluss der Sunrise Phase:
        self.log_action("Sunrise Phase abgeschlossen")
        self.sunrise_phase_active = False

    async def start_sunset_phase(self):
        """Führt die Logik des Sonnenuntergangs aus (z. B. allmähliches Herunterfahren der Helligkeit)."""
        # Beispiel: Verringere die Helligkeit in kleinen Schritten
        for step in range(10):
            new_voltage = self.calculate_voltage_for_sunset(step)
            await self.turn_on(brightness_pct=new_voltage)
            await asyncio.sleep(30)
        self.log_action("Sunset Phase abgeschlossen")
        self.sunset_phase_active = False

    def calculate_voltage_for_sunrise(self, step):
        # Beispielhafte Berechnung: linear von minVoltage bis maxVoltage
        return self.minVoltage + (self.currentMinMax["max"] - self.minVoltage) * ((step + 1) / 10)

    def calculate_voltage_for_sunset(self, step):
        # Analog, aber umgekehrt
        return self.maxVoltage - (self.currentMinMax["max"] - self.minVoltage) * ((step + 1) / 10)

   
    ## Actions
    async def toggleLight(self, lightState):
        self.islightON = lightState

        # Überprüfe, ob die Lichtsteuerung aktiviert ist
        self.ogbLightControl = self.dataStore.getDeep("controlOptions.lightbyOGBControl")
        if not self.ogbLightControl:
            self.log_action("Light control is disabled.")
            return

        _LOGGER.debug(f"{self.deviceName} LIGHT STATE: {lightState} ISRUNNING: {self.isRunning}")

        # Fallback-Logik: Sicherstellen, dass der tatsächliche Zustand mit `lightState` übereinstimmt
        if lightState and not self.isRunning:
            # Licht soll eingeschaltet werden, Gerät ist aber nicht aktiv
            self.log_action("Fallback: Device is off, but lightState is True. Turning ON.")
            await self.turn_on()
            self.islightON = True
            return  # Vermeidet Doppelsteuerung, Fallback überschreibt normale Logik

        if not lightState and self.isRunning:
            # Licht soll ausgeschaltet werden, Gerät ist aber noch aktiv
            self.log_action("Fallback: Device is on, but lightState is False. Turning OFF.")
            await self.turn_off()
            self.islightON = False
            return  # Vermeidet Doppelsteuerung, Fallback überschreibt normale Logik

        # Licht einschalten
        if lightState:
            if self.isRunning:
                self.log_action("Device Already ON")
            else:
                await self.turn_on()
                self.islightON = True
                self.log_action("Turn Light Switch ON")

        # Licht ausschalten
        elif not lightState:
            if not self.isRunning:
                self.log_action("Device Already OFF")
            else:
                await self.turn_off()
                self.islightON = False
                self.log_action("Turn Light Switch OFF")

        # Sicherheitsfall, falls der `lightState` ungültig ist
        else:
            self.log_action("Invalid light state provided.")
       
    async def increaseAction(self, data):
        """Erhöht die Spannung."""
        if self.islightON == False:
            self.log_action("Not Allowed: LightSchedule is 'OFF'")
            return
        if self.ogbLightControl == False:
            self.log_action("Not Allowed: OGBLightControl is 'OFF'")
            return
        
        if self.isDimmable:
            vpdLightControl = self.dataStore.getDeep("controlOptionData.vpdLightControl")
            if not vpdLightControl:
                return
                        
            new_voltage = self.change_voltage(increase=True)
            if new_voltage is not None:
                self.log_action("IncreaseAction")
                await self.turn_on(brightness_pct=new_voltage)

    async def reduceAction(self, data):
        """Reduziert die Spannung."""
        if self.islightON == False:
            self.log_action("Not Allowed: LightSchedule is 'OFF'")
            return
        if self.ogbLightControl == False:
            self.log_action("Not Allowed: OGBLightControl is 'OFF'")
            return

        if self.isDimmable:
            vpdLightControl = self.dataStore.getDeep("controlOptionData.vpdLightControl")
            if not vpdLightControl:
                return
                
            new_voltage = self.change_voltage(increase=False)
            if new_voltage is not None:
                self.log_action("ReduceAction")
                await self.turn_on(brightness_pct=new_voltage)
                    
    def log_action(self, action_name):
        """Protokolliert die ausgeführte Aktion mit tatsächlicher Spannung."""
        if self.voltage is not None:
            actual_voltage = self.calculate_actual_voltage(self.voltage)
            log_message = f"{self.deviceName} Voltage: {self.voltage}% (Actual: {actual_voltage:.2f} V)"
        else:
            log_message = f"{self.deviceName} Voltage: Not Set"
        #_LOGGER.warn(f"{self.deviceName} - {action_name}: {log_message}")
