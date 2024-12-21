import smbus
import logging
import sys
import time

# Logging einrichten
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class tasten_Sensor:
    def __init__(self, address=0x20, i2c_bus=None, debug=False):
        """
        Initialisiert den Tasten-Sensor (MCP23008) und konfiguriert die I/O-Ports.
        """
        self.debug = debug
        self.BUSNR = 1
        self.ADDR = address  # Standardadresse für den MCP23008
        self.IODIRA = 0x00   # Register für I/O-Richtung (Port B)
        self.GPIOA = 0x09    # Register für I/O Manipulation von Port B (GPIO)
        
        # Initialisiere den I2C-Bus
        self.i2c_bus = smbus.SMBus(self.BUSNR)
        
        # Setze alle Pins des Port B als Eingang (0xFF bedeutet alle Eingänge)
        self.i2c_bus.write_byte_data(self.ADDR, self.IODIRA, 0xFF)
        
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
            data = self.i2c_bus.read_byte_data(self.ADDR, self.GPIOA)
            
            # Speichere die Daten für zukünftige Fehlerbehandlung
            self.olddata = data

            if self.debug:
                logging.debug(f"Tastenstatus: {bin(data)} (Binarwert)")

            # Rückgabe des gelesenen Datenwerts
            return data
        except Exception as e:
            # Fehlerbehandlung, falls ein Fehler auftritt
            logging.error(f"Fehler beim Lesen des Tastenstatus: {str(e)}")
            
            # Gib den letzten gültigen Wert zurück
            return self.olddata

def get_tasten(sensor):
    """
    Ruft den aktuellen Ruderausschlag ab.
    Gibt den berechneten Winkel in Grad zurück.
    """
    try:
        # Lese den aktuellen Winkel
        data = sensor.read_sensor()
        if data is not None:
            logging.info(f"Aktueller Ruderausschlag: {data}")
            return data
        else:
            logging.warning("Fehler beim Abrufen der Tasten.")
            return None
    except Exception as e:
        logging.error(f"Fehler bei der Tastenauslesung: {str(e)}")
        return None


