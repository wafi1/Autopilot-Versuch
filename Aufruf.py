from ruderausschlag_sensor import ruderlage_Sensor, get_ruderausschlag

# Initialisiere den Sensor
sensor = ruderlage_Sensor(debug=True)

# Beispiel: Abrufen und Weiterverarbeiten des Ruderausschlags
if __name__ == "__main__":
    try:
        # Hole den aktuellen Ruderausschlag
        ruderausschlag = get_ruderausschlag(sensor)
        
        # Verarbeite den Wert weiter (z. B. Ausgabe oder Verwendung in Berechnungen)
        if ruderausschlag is not None:
            print(f"Der aktuelle Ruderausschlag beträgt {ruderausschlag:.2f}°.")
        else:
            print("Es konnte kein Ruderausschlag abgerufen werden.")
            
    except KeyboardInterrupt:
        print("Messung abgebrochen.")
