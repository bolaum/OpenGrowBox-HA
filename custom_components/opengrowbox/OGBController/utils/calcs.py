import math
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)

# Berechne Durchschnittswert aus einer Liste (asynchron)
def calculate_avg_value(data=[]):
    total = 0
    count = 0

    for entry in data:
        # Prüfe, ob der Eintrag ein Dictionary ist
        if not isinstance(entry, dict):
            _LOGGER.warn(f"Ignoring non-dictionary entry: {entry}")
            continue

        # Extrahiere den 'value'-Wert
        value = entry.get("value")
        if value is None:
            _LOGGER.warn(f"Ignoring None value for entry: {entry}")
            continue

        try:
            # Konvertiere den Wert in float
            value = float(value)
            total += value
            count += 1
        except ValueError:
            _LOGGER.warn(f"Ignoring non-numeric value '{value}' for entry: {entry}")
        except Exception as e:
            _LOGGER.error(f"Unexpected error for entry {entry}: {e}")

    if count == 0:
        return "unavailable"

    avg_value = total / count
    return round(avg_value, 2)

# Berechne aktuellen VPD (asynchron)
def calculate_current_vpd(temp, humidity, leaf_offset):
    try:
        temp = float(temp)
        humidity = float(humidity)
        leaf_temp = temp - float(leaf_offset)
    except (ValueError, TypeError):
        return None

    if temp is None or humidity is None or leaf_temp is None:
        return None

    sdp_luft = 0.6108 * math.exp((17.27 * temp) / (temp + 237.3))
    sdp_blatt = 0.6108 * math.exp((17.27 * leaf_temp) / (leaf_temp + 237.3))
    adp = (humidity / 100) * sdp_luft
    vpd = sdp_blatt - adp

    _LOGGER.debug(f"VPD-Calculation got {round(vpd, 2)}")
    return round(vpd, 2)

# Berechne perfekten VPD (asynchron)
def calculate_perfect_vpd(vpd_range, tolerance_percent):

    if not isinstance(vpd_range, (list, tuple)) or len(vpd_range) != 2:
        raise ValueError("vpd_range must be a list or tuple with exactly two numbers.")

    try:
        vpd_min = float(vpd_range[0])
        vpd_max = float(vpd_range[1])
        tolerance_percent = float(tolerance_percent)
    except (ValueError, TypeError):
        raise ValueError("Invalid inputs for vpd_range or tolerance_percent.")

    average_vpd = (vpd_min + vpd_max) / 2
    tolerance = (tolerance_percent / 100) * average_vpd
    
    return {
        "perfection": round(average_vpd, 3),
        "perfect_min": round(average_vpd - tolerance, 3),
        "perfect_max": round(average_vpd + tolerance, 3),
    }

# Berechne Taupunkt (asynchron)
def calculate_dew_point(temp, humidity):
    try:
        temp = float(temp)
        humidity = float(humidity)
    except (ValueError, TypeError):
        return "unavailable"

    a = 17.27
    b = 237.7

    gamma = (a * temp) / (b + temp) + math.log(humidity / 100)
    dew_point = (b * gamma) / (a - gamma)

    return round(dew_point, 2)

# Berechne DewPointVPD (asynchron)
async def calc_dew_vpd(air_temp, dew_point):
    try:
        air_temp = float(air_temp)
        dew_point = float(dew_point)
    except (ValueError, TypeError):
        return {
            "dewpoint_vpd": None,
            "vapor_pressure_actual": None,
            "vapor_pressure_saturation": None,
        }

    sdp_luft = 0.6108 * math.exp((17.27 * air_temp) / (air_temp + 237.3))
    adp = 0.6108 * math.exp((17.27 * dew_point) / (dew_point + 237.3))
    dew_vpd = sdp_luft - adp

    vapor_pressure_actual = 6.11 * (10 ** ((7.5 * dew_point) / (237.3 + dew_point)))
    vapor_pressure_saturation = 6.11 * (10 ** ((7.5 * air_temp) / (237.3 + air_temp)))

    return {
        "dewpoint_vpd": round(dew_vpd, 3),
        "vapor_pressure_actual": round(vapor_pressure_actual, 2),
        "vapor_pressure_saturation": round(vapor_pressure_saturation, 2),
    }

# Berechne DewPointVPD (Based on Dewpoint/TEMP)
def calc_dew_vpd(air_temp, dew_point):
    try:
        air_temp = float(air_temp)
        dew_point = float(dew_point)
    except (ValueError, TypeError):
        return {
            "dewpoint_vpd": None,
            "vapor_pressure_actual": None,
            "vapor_pressure_saturation": None,
        }

    sdp_luft = 0.6108 * math.exp((17.27 * air_temp) / (air_temp + 237.3))
    adp = 0.6108 * math.exp((17.27 * dew_point) / (dew_point + 237.3))
    dew_vpd = sdp_luft - adp

    vapor_pressure_actual = 6.11 * (10 ** ((7.5 * dew_point) / (237.3 + dew_point)))
    vapor_pressure_saturation = 6.11 * (10 ** ((7.5 * air_temp) / (237.3 + air_temp)))

    return {
        "dewpoint_vpd": round(dew_vpd, 3),
        "vapor_pressure_actual": round(vapor_pressure_actual, 2),
        "vapor_pressure_saturation": round(vapor_pressure_saturation, 2),
    }

# Berechne SharkMouse VPD (Based on TEMP/HUM/VPD)
def calc_shark_mouse_vpd(temp, humidity, leaf_offset=0):
    try:
        temp = float(temp)
        humidity = float(humidity)
        leaf_temp = temp - float(leaf_offset)
    except (ValueError, TypeError):
        return None

    sdp_luft = 0.6108 * math.exp((17.27 * temp) / (temp + 237.3))
    sdp_blatt = 0.6108 * math.exp((17.27 * leaf_temp) / (leaf_temp + 237.3))
    adp = (humidity / 100) * sdp_luft
    vpd = sdp_blatt - adp

    return round(vpd, 2)
