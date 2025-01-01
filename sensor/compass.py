import logging
import serial

# Initialisiere das Logging
logging.basicConfig(level=logging.DEBUG)

class compass_Sensor:
    """ Tilt adjusted Compass sensor CMP10 over I2C. """

    def __init__(self):
        # Variable für den letzten Heading-Wert als Instanzvariable
        self.oldheading = 0.0
        
        # Optional: Debug Mode aktivieren
        self.debug = True

    def read_sensor(self):
        """ Liest die Sensordaten des Kompasses. """
        try:
            # Öffnen des seriellen Ports
            port = "/dev/ttyUSB0"
            ser = serial.Serial(port, baudrate=4800, timeout=0.5)
            
            # Lese eine Zeile vom Sensor
            line = ser.readline()
            line2 = line.decode('latin-1')

            if line2.startswith("$HCHDG"):
                # Extrahiere die Heading-Daten
                KPK = line2.split(",")[1]
                KPK = float(KPK)
                MW = line2.split(",")[4]
                MW = float(MW)
                WE = line2.split(",")[5]
                
                # Berechne den Heading-Wert basierend auf der Ost-/West-Angabe
                if WE.startswith("W"):
                    KPK = KPK + MW
                else:
                    KPK = KPK - MW
                
                # Handle Werte über 360 und unter 0
                if KPK > 360:
                    KPK = KPK - 360
                elif KPK < 0:
                    KPK = 360 + KPK

                heading = KPK
                self.oldheading = KPK  # Speichere den neuen Wert

            else:
                heading = self.oldheading  # Nutze den alten Wert, falls keine gültigen Daten empfangen wurden

        except serial.SerialException as e:
            logging.error(f"SENSOR:\tCMPS10\tFehler bei der seriellen Verbindung: {str(e)}")
            heading = self.oldheading
        
        except ValueError:
            logging.error("SENSOR:\tCMPS10\tFehler bei der Umwandlung der Daten in einen Float.")
            heading = self.oldheading
        
        except Exception as e:
            logging.error("SENSOR:\tCMPS10\tUnbekannter Fehler: %s", str(e))
            heading = self.oldheading
        
        finally:
            # Stelle sicher, dass der Serial-Port immer geschlossen wird
            if 'ser' in locals() and ser.is_open:
                ser.close()
        
        return heading

# Beispiel zum Testen der Sensor-Klasse
if __name__ == "__main__":
    sensor = compass_Sensor()
    
    # Simuliere das Lesen von Sensordaten
    heading = sensor.read_sensor()
    print(f"Aktueller Heading-Wert: {heading}")
