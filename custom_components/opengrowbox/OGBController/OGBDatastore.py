import logging


_LOGGER = logging.getLogger(__name__)

class SimpleEventEmitter:
    def __init__(self):
        self.events = {}  # Speichert Events und ihre Listener

    def on(self, event_name, callback):
        """Abonniere ein Event."""
        if event_name not in self.events:
            self.events[event_name] = []
        self.events[event_name].append(callback)

    def off(self, event_name, callback):
        """Entferne einen Listener von einem Event."""
        if event_name in self.events:
            self.events[event_name] = [cb for cb in self.events[event_name] if cb != callback]

    def emit(self, event_name, *args, **kwargs):
        """Trigger ein Event und rufe alle zugehörigen Listener auf."""
        if event_name in self.events:
            for callback in self.events[event_name]:
                callback(*args, **kwargs)

    async def emit_async(self, event_name, *args, **kwargs):
        """Asynchrones Event auslösen."""
        if event_name in self.events:
            for callback in self.events[event_name]:
                if callable(callback):
                    await callback(*args, **kwargs)

class DataStore(SimpleEventEmitter):
    def __init__(self, initial_state):
        super().__init__()
        # Falls initial_state None ist, benutze das leere OGBConf Objekt
        self.state = initial_state
        
    def __repr__(self):
        return (f"Datastore State:'{self.state}'")

    def get(self, key):
        """Ruft den Wert für einen Schlüssel ab."""
        return getattr(self.state, key, None)

    def set(self, key, value):
        """Setzt einen neuen Wert und löst Events aus, falls der Wert geändert wurde."""
        if getattr(self.state, key, None) != value:
            setattr(self.state, key, value)
            self.emit(key, value)

    def getDeep(self, path):
        """Ruft verschachtelte Daten anhand eines Pfads ab (für Attribute oder Schlüssel in Dictionaries)."""
        keys = path.split(".")
        data = self.state
        for key in keys:
            if isinstance(data, dict):  # Falls `data` ein Dictionary ist
                data = data.get(key, None)
            elif hasattr(data, key):  # Falls `data` ein Objekt ist
                data = getattr(data, key)
            else:
                return None  # Schlüssel oder Attribut existiert nicht
        return data


    def setDeep(self, path, value):
        """Setzt einen Wert in verschachtelten Daten und löst Events aus."""
        keys = path.split(".")
        data = self.state
        for key in keys[:-1]:
            if isinstance(data, dict):
                if key not in data:
                    data[key] = {}  # Initialisiere verschachteltes Dictionary, falls es nicht existiert
                data = data[key]
            elif hasattr(data, key):
                data = getattr(data, key)
            else:
                raise AttributeError(f"Cannot access '{key}' on '{type(data).__name__}'")
        
        last_key = keys[-1]
        if isinstance(data, dict):
            data[last_key] = value
            self.emit(path, value)
        elif hasattr(data, last_key):
            if getattr(data, last_key) != value:
                setattr(data, last_key, value)
                self.emit(path, value)
        else:
            raise AttributeError(f"Cannot set '{last_key}' on '{type(data).__name__}'")
