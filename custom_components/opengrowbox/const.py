DOMAIN = "opengrowbox"
VERSION = "1.3.0"
URL_BASE = "/ogb"
PREM_WS_API = "wss://prem.opengrowbox.net"
#PREM_WS_API = "ws://10.1.1.140:3001"

DEFAULT_COOLDOWN_MINUTES = {
    "canHumidify": 3,      # Befeuchter braucht Zeit
    "canDehumidify": 4,    # Entfeuchter braucht noch mehr Zeit
    "canHeat": 1,          # Heizung reagiert relativ schnell
    "canCool": 2,          # Kühlung braucht etwas Zeit
    "canExhaust": 1,       # Abluft reagiert schnell
    "canIntake": 1,        # Zuluft reagiert schnell
    "canVentilate": 1,     # Ventilation reagiert schnell
    "canLight": 1,         # Licht reagiert sofort, aber VPD-Effekt braucht Zeit
    "canCO2": 2,           # CO2 braucht Zeit zur Verteilung
    "canClimate": 2        # Klima-System braucht Zeit
}