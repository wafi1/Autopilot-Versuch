from ruderlage import ruderlage_Sensor

sensor = ruderlage_Sensor(debug=True)

try:
    winkel = sensor.read_sensor()
    if winkel is not None:
        print(f"Ruder-Winkel: {winkel}")
    else:
        print("Kein gültiger Winkelwert vom Sensor.")
except Exception as e:
    print(f"Fehler beim Lesen des Sensors: {e}")
