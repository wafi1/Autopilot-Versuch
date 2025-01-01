import smbus
import time
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)

# MCP3426 I2C Adressierung und Konstanten
VREF = 2.048  # Referenzspannung in Volts
RESOLUTION = 12  # Auflösung des ADC in Bits
GAIN = 1  # Verstärkung (x1)

# Faktor zur Berechnung des Winkels
K = 0.051
OFFSET = -2.1

class ruderlage_Sensor:
    def __init__(self, address=0x68, i2c_bus=None, debug=False):
        """
        Initialisiert den Ruderlage-Sensor mit I2C-Adresse und einem bereits initialisierten I2C-Bus.
        """
        self.debug = debug
        self.sensor_address = address
        self.i2c_bus = i2c_bus  # I2C-Bus wird übergeben

        if i2c_bus is None:
            self.i2c_bus = smbus.SMBus(1)  # I2C-Bus 1 auf Raspberry Pi
        else:
            self.i2c_bus = i2c_bus
        
        # Sensor vorbereiten (Initialisierung durch Schreiben in Register)
        self._initialize_sensor()

    def _initialize_sensor(self):
        """
        Initialisiert den Sensor durch das Schreiben in I2C-Register.
        """
        try:
            # Beispielhafte I2C-Initialisierung (könnte für deinen Sensor variieren)
            self.i2c_bus.write_byte(self.sensor_address, 0x80)
            self.i2c_bus.write_byte(self.sensor_address, 0x00)
            self.i2c_bus.write_byte(self.sensor_address, 0x10)
            self.i2c_bus.write_byte(self.sensor_address, 0x00)
            self.i2c_bus.write_byte(self.sensor_address, 0x00)
            
            #logging.info("Sensor erfolgreich initialisiert.")
            
        except Exception as e:
            #logging.error(f"Fehler beim Initialisieren des Sensors: {str(e)}")
            raise           

    def read_sensor(self):
        """
        Liest den Sensorwert und berechnet den Winkel aus den ADC-Daten.
        """
        try:
            # Lese die ADC-Werte vom Sensor (2 Byte)
            data = self.i2c_bus.read_i2c_block_data(self.sensor_address, 0x00, 2)
            value = (data[0] << 8) | data[1]  # Kombiniere die beiden Bytes zu einem Wert
            
            # Falls der Wert größer oder gleich 32768 ist, den Wert anpassen
            if value >= 32768:
                value = 65536 - value

            # Berechne den Winkel aus dem ADC-Wert
            voltage = (VREF * value) / (2 ** RESOLUTION)  # Berechne die Spannung
            angle = ((2 * voltage * value) / (2 ** RESOLUTION) * 1000 - 931) * K + OFFSET

            # Debugging-Ausgabe
            #logging.debug(f"SENSOR:\truderlage\tWinkel {angle:.2f}°")

            return angle * -1  # Winkel invertieren, falls notwendig
        except Exception as e:
            logging.error(f"Fehler beim Lesen des Ruder Sensors: {str(e)}")
            return None


# Funktion zur Messung des Ruderausschlags (rückgabewert in Grad)
def get_ruderausschlag(sensor):
    """
    Ruft den aktuellen Ruderausschlag ab.
    Gibt den berechneten Winkel in Grad zurück.
    """
    try:
        # Lese den aktuellen Winkel
        angle = sensor.read_sensor()
        if angle is not None:
            logging.info(f"Aktueller Ruderausschlag: {angle:.2f}°")
            return angle
        else:
            logging.warning("Fehler beim Abrufen des Ruderausschlags.")
            return None
    except Exception as e:
        #logging.error(f"Fehler bei der Ruderausschlagmessung: {str(e)}")
        return None
