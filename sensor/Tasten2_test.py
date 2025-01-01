import smbus
import logging
import time

# Logging einrichten
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class TASTEN_Sensor:
    def __init__(self, address=0x20, i2c_bus=None, debug=False):
        """
        Initialisiert den Tasten-Sensor (MCP23008) und konfiguriert die I/O-Ports.
        """
        self.debug = debug
        self.BUSNR = 1
        self.ADDR = address  # Standardadresse für den MCP23008
        self.IODIRB = 0x00   # Register für I/O-Richtung (Port B)
        self.GPIOB = 0x09    # Register für I/O Manipulation von Port B (GPIO)
        
        # Initialisiere den I2C-Bus
        self.i2c_bus = smbus.SMBus(self.BUSNR)
        
        # Setze alle Pins des Port B als Eingang (0xFF bedeutet alle Eingänge)
        self.i2c_bus.write_byte_data(self.ADDR, self.IODIRB, 0xFF)
        
        # Historische Daten, um bei Fehlern zurückzugreifen
        self.olddata = None

        if self.debug:
            logging.debug(f"Sensor mit Adresse {hex(self.ADDR)} auf I2C-Bus {self.BUSNR} initialisiert.")

    def read_sensor(self):
        """
        Liest den aktuellen Status der Tasten (GPIOB) und gibt den Wert zurück.
        """
        try:
            # Lese den Wert von Port B
            data = self.i2c_bus.read_byte_data(self.ADDR, self.GPIOB)
            
            # Speichere die Daten für zukünftige Fehlerbehandlung
            self.olddata = data

            if self.debug:
                # Debug-Ausgabe des Rohwerts vom MCP23008 und der Binärdarstellung
                logging.debug(f"Tastenstatus (Rohwert): {data} (Dezimalwert), {bin(data)} (Binarwert)")

            # Rückgabe des gelesenen Datenwerts
            return data
        except Exception as e:
            # Fehlerbehandlung, falls ein Fehler auftritt
            logging.error(f"Fehler beim Lesen des Tastenstatus: {str(e)}")
            
            # Gib den letzten gültigen Wert zurück
            return self.olddata

# Beispiel zum Testen der Tasten-Sensor-Klasse
if __name__ == "__main__":
    sensor = TASTEN_Sensor(debug=True)

    # Simuliere das Lesen der Tasten alle 1 Sekunde
    try:
        while True:
            # Lese den Sensorwert und gebe ihn aus
            data = sensor.read_sensor()
            if data is not None:
                # Zusätzliche Ausgabe der Tastenstatuswerte für mehr Klarheit
                logging.info(f"Aktueller Tastenstatus (Dezimalwert): {data}")
            else:
                logging.warning("Kein gültiger Tastenstatus verfügbar.")
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Messung abgebrochen.")
