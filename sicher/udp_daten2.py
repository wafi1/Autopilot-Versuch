import socket
import logging

# Set default socket timeout
socket.setdefaulttimeout(20)

# Initialisiere das Logging
logging.basicConfig(level=logging.DEBUG)

class OPENCPN_Sensor:

    def __init__(self):
        self.oldheading = 0.0
        self.debug = True        
        # Initialisieren des Sockets
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', 10110))

        # Variablen für die Sensorwerte
        self.oldKPK = 0
        self.oldDist = 0
        self.oldspeed = 0

    def read_sensor(self):
        """ Liest die Sensordaten vom Socket und verarbeitet sie. """
        try:
            # Empfange Daten vom Socket (maximal 1024 Bytes)
            data, addr = self.sock.recvfrom(1024)
            datalist = data.decode('utf-8').split(',')

            # Überprüfen, ob es sich um den erwarteten Datensatz handelt
            if datalist[0] == "$ECRMB":
                # Parse die Daten
                KPK = float(datalist[11])
                Dist = float(datalist[10])
                speed = float(datalist[12])

                # Speichern der aktuellen Werte für den nächsten Durchlauf
                self.oldKPK = KPK
                self.oldDist = Dist
                self.oldspeed = speed
            else:
                # Rückgabe der alten Werte, falls der Datensatz nicht passt
                KPK = self.oldKPK
                Dist = self.oldDist
                speed = self.oldspeed

                # Debugging-Ausgabe
                if self.debug:
                    logging.debug("SENSOR:\tOPENCPN\tKPK: %f, Dist: %f, Speed: %f", KPK, Dist, speed)

            return KPK, Dist, speed

        except socket.timeout:
            logging.warning("SENSOR:\tOPENCPN\tTimeout beim Empfangen der Daten.")
            return self.oldKPK, self.oldDist, self.oldspeed
        
        except ValueError:
            logging.error("SENSOR:\tOPENCPN\tFehler bei der Umwandlung der Daten in einen Float.")
            return self.oldKPK, self.oldDist, self.oldspeed
        
        except Exception as e:
            logging.error("SENSOR:\tOPENCPN\tUnbekannter Fehler: %s", str(e))
            return self.oldKPK, self.oldDist, self.oldspeed

    def close_socket(self):
        """ Stellt sicher, dass der Socket geschlossen wird, wenn er nicht mehr benötigt wird. """
        if self.sock:
            self.sock.close()

# Beispiel zum Testen der Sensor-Klasse
if __name__ == "__main__":
    sensor = OPENCPN_Sensor()

    try:
        # Simuliere das Lesen von Sensordaten
        KPK, Dist, speed = sensor.read_sensor()
        print(f"Aktueller KPK-Wert: {KPK}")
        print(f"Aktuelle Distanz: {Dist}")
        print(f"Aktuelle Geschwindigkeit: {speed}")
    finally:
        # Stelle sicher, dass der Socket geschlossen wird, wenn das Programm beendet wird.
        sensor.close_socket()
