from datetime import datetime

def set_drying_start_time(dryStartTime):
    if not dryStartTime or not isinstance(dryStartTime, datetime):
        dryStartTime = datetime.now()  # Erstelle ein gültiges datetime-Objekt
        print(f"Startzeit wurde gesetzt:")
        return dryStartTime