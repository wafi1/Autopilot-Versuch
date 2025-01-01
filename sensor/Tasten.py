import smbus
import logging
import sys
import os
import time
from raspberrypi import i2c_bus

# Logging einrichten
#logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class TASTEN_Sensor:
    def __init__(self, address=0x20, i2c_bus=None, debug=False):
        self.debug = debug
        self.ADDR = address  # Standardadresse für den MCP23008
        self.IODIRB = 0x00   # Register für I/O-Richtung (Port B)
        self.GPIOB = 0x09    # Register für I/O Manipulation von Port B (GPIO)

        # Überprüfen Sie, ob der i2c_bus korrekt übergeben wurde. Falls nicht, default auf Bus 1
        if i2c_bus is None:
            self.i2c_bus = smbus.SMBus(1)  # I2C-Bus 1 auf Raspberry Pi
        else:
            self.i2c_bus = i2c_bus

        try:
            # Versuche die Kommunikation zu testen, indem du das IODIRB-Register liest
            iodirb_value = self.i2c_bus.read_byte_data(self.ADDR, self.IODIRB)
            logging.debug(f"Erfolgreich IODIRB Register gelesen: {bin(iodirb_value)}")
        except Exception as e:
            logging.error(f"Fehler beim Initialisieren des Sensors: {str(e)}")
            raise

        # Historische Daten, um bei Fehlern zurückzugreifen
        self.olddata = None

        if self.debug:
            logging.debug(f"Sensor mit Adresse {hex(self.ADDR)} auf I2C-Bus {self.i2c_bus} initialisiert.")


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
                logging.debug(f"Tastenstatus: (data)")

            # Rückgabe des gelesenen Datenwerts
            return data
        except Exception as e:
            # Fehlerbehandlung, falls ein Fehler auftritt
            logging.error(f"Fehler beim Lesen des Tastenstatus: {str(e)}")
        
            # Geben Sie den alten Wert zurück, wenn ein Fehler auftritt
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
                logging.info(f"Aktueller Tastenstatus: data)")
            else:
                logging.warning("Kein gültiger Tastenstatus verfügbar.")
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Messung abgebrochen.")
