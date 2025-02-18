from dataclasses import is_dataclass, asdict
import asyncio
import logging
import inspect
import json

_LOGGER = logging.getLogger(__name__)

class OGBEventManager:
    def __init__(self, hass, ogb_model):
        self.name = "OGB Event Manager"
        self.hass = hass
        self.ogb_model = ogb_model
        self.listeners = {}  # Speichert alle Listener (synchron + asynchron)

    def __repr__(self):
        return f"Current Listeners: {self.listeners}"

    def on(self, event_name, callback):
        """Registriere einen Listener (synchron oder asynchron) für ein spezifisches Event."""
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)

    def remove(self, event_name, callback):
        """Entferne einen spezifischen Listener."""
        if event_name in self.listeners and callback in self.listeners[event_name]:
            self.listeners[event_name].remove(callback)

    async def _call_listener(self, callback, data):
        """Rufe einen Listener auf, synchron oder asynchron."""
        try:
            if inspect.iscoroutinefunction(callback):  # Prüfe, ob die Funktion asynchron ist
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            _LOGGER.error(f"Fehler beim Aufruf des Listeners für '{callback}': {e}")

    async def emit(self, event_name, data, haEvent=False):
        """Event auslösen, erkennt automatisch synchrone oder asynchrone Listener.
        Wenn haEvent=True, wird das Event auch an Home Assistant gesendet."""
        
        if haEvent:
            # Event an Home Assistant senden (nicht blockierend)
            asyncio.create_task(self.emit_to_home_assistant(event_name, data))

        # Interne Event-Verarbeitung
        if event_name in self.listeners:
            for callback in self.listeners[event_name]:
                if inspect.iscoroutinefunction(callback):
                    asyncio.create_task(callback(data))  # Asynchronen Listener aufrufen
                else:
                    try:
                        callback(data)  # Synchronen Listener aufrufen
                    except Exception as e:
                        _LOGGER.error(f"Fehler beim synchronen Listener: {e}")

    def emit_sync(self, event_name, data, haEvent=False):
        """Synchrones Event auslösen (für synchrone Kontexte).
        Wenn haEvent=True, wird das Event auch an Home Assistant gesendet."""
        asyncio.create_task(self.emit(event_name, data, haEvent))

    async def emit_to_home_assistant(self, event_name, event_data):
        """Sende ein Event an Home Assistant über den Event-Bus."""
        try:
            # Wenn event_data ein Dataclass-Objekt ist, in ein Dictionary umwandeln
            if is_dataclass(event_data):
                event_data = asdict(event_data)

            if hasattr(self.hass, "bus"):
                self.hass.bus.fire(event_name, event_data)
                _LOGGER.info(f"Event-Bus Event '{event_name}' erfolgreich gesendet.")
            else:
                _LOGGER.warning(f"Kein gültiger Event-Kanal für '{event_name}' verfügbar!")
        except Exception as e:
            _LOGGER.error(f"Fehler beim Senden des Events '{event_name}': {e}")