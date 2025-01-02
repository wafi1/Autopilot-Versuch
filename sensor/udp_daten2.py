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
        self.oldtrack = 0

        
    def read_sensor(self):
        """ Liest die Sensordaten vom Socket und verarbeitet sie. """
        try:
            # Empfange Daten vom Socket (maximal 1024 Bytes)
            data, addr = self.sock.recvfrom(1024)
            datalist = data.decode('utf-8').split(',')

            # Überprüfen, um welchen Datensatz es sich handelt
            if datalist[0] == "$ECRMB":
                # Verarbeiten des ECRMB-Datensatzes
                try:
                    KPK = float(datalist[11])
                    Dist = float(datalist[10])
                except ValueError:
                    KPK = self.oldKPK
                    Dist = self.oldDist
                speed = self.oldspeed  # Geschwindigkeit bleibt unverändert
                track = self.oldtrack

                # Speichern der aktuellen Werte
                self.oldKPK = KPK
                self.oldDist = Dist

            elif datalist[0] == "$RMC":
                # Verarbeiten des RMC-Datensatzes
                try:
                    speed = float(datalist[7])  # Knoten
                    track = float(datalist[8])  # Knoten
                    if speed == 0:
                        speed = 6
                except ValueError:
                    speed = self.oldspeed
                    track = self.oldtrack
                KPK = self.oldKPK  # Kurs bleibt unverändert
                Dist = self.oldDist  # Distanz bleibt unverändert

                # Speichern der aktuellen Geschwindigkeit
                self.oldspeed = speed
                self.oldtrack = track

            else:
                # Rückgabe der alten Werte, falls kein erwarteter Datensatz vorliegt
                KPK = self.oldKPK
                Dist = self.oldDist
                speed = 6
                track = self.oldtrack

            # Debugging-Ausgabe
            if self.debug:
                logging.debug("SENSOR:\tOPENCPN\tKPK: %f, Dist: %f, Speed: %f, Track: %f", KPK, Dist, speed, track)

            return KPK, Dist, speed, track

        except socket.timeout:
            logging.warning("SENSOR:\tOPENCPN\tTimeout beim Empfangen der Daten.")
            return self.oldKPK, self.oldDist, self.oldspeed, self.oldtrack

        except Exception as e:
            logging.error("SENSOR:\tOPENCPN\tUnbekannter Fehler: %s", str(e))
            return self.oldKPK, self.oldDist, self.oldspeed, self.oldtrack
    


    def close_socket(self):
        """ Stellt sicher, dass der Socket geschlossen wird, wenn er nicht mehr benötigt wird. """
        if self.sock:
            self.sock.close()

# Beispiel zum Testen der Sensor-Klasse
if __name__ == "__main__":
    sensor = OPENCPN_Sensor()

    try:
        # Simuliere das Lesen von Sensordaten
        while True:
            KPK, Dist, speed = sensor.read_sensor()
            print(f"Aktueller KPK-Wert: {KPK}")
            print(f"Aktuelle Distanz: {Dist}")
            print(f"Aktuelle Geschwindigkeit: {speed}")
            print(f"Aktueller GPS Kurs: {track}")
    finally:
        # Stelle sicher, dass der Socket geschlossen wird, wenn das Programm beendet wird.
        sensor.close_socket()
