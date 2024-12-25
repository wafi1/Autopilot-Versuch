import logging
import logging.handlers
import socket
import smbus
import os
import platform
import subprocess
import time
import RPi.GPIO as GPIO
from vehicle.drive_controller import Drive_Controller
from sensor.Tasten import TASTEN_Sensor
from sensor.ruderlage import ruderlage_Sensor


#logging.error(f"Fehler bei der Initialisierung des Drive_Controllers: {e}")

class FishPiConfig(object):
    _devices = []
    _root_dir = os.path.join(os.getenv("HOME"), "fishpi")

    def __init__(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        console = logging.StreamHandler()
        logger.addHandler(console)

        # Verzeichnisstruktur erstellen
        if not os.path.exists(self._root_dir):
            os.makedirs(self._root_dir)

        log_file_stem = os.path.join(self._root_dir, 'fishpi_%s.log' % time.strftime('%Y%m%d_%H%M%S'))
        handler = logging.handlers.RotatingFileHandler(log_file_stem, backupCount=50)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Geräte initialisieren
        self.shared_i2c_bus = smbus.SMBus(1)
        try:
            self.drive_controller = Drive_Controller(i2c_bus=self.shared_i2c_bus, debug=True)
            logging.info("Drive_Controller erfolgreich initialisiert.")
        except Exception as e:
            logging.error(f"Fehler bei der Initialisierung des Drive_Controllers: {e}")
            self.drive_controller = None  # Als Fallback auf None setzen

        self.tasten_sensor = None
        self.ruder_sensor = None
        self.compass_sensor = None
        self.udp_sensor = None

        self._vehicle_constants = VehicleConstants()

    @property
    def vehicle_constants(self):
        return self._vehicle_constants

    @property
    def server_name(self):
        return self._server_name

    @server_name.setter
    def server_name(self, value):
        self._server_name = value

    @property
    def config_file(self):
        return os.path.join(self._root_dir, ".fishpi_config")

    @property
    def navigation_data_path(self):
        return os.path.join(self._root_dir, "navigation")

    @property
    def logs_path(self):
        return os.path.join(self._root_dir, "logs")

    def resources_folder(self):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    @property
    def devices(self):
        return self._devices

    def configure_devices(self, debug=False):
        if not(platform.system() == "Linux"):
            logging.info("CFG:\tNicht auf einem Linux-Distro ausgeführt. I2C oder andere Geräte werden nicht konfiguriert.")
            self.set_dummy_devices()
            return

        try:
            logging.info("CFG:\tKonfiguration von I2C-Geräten wird durchgeführt...")
            i2c_addresses = self.scan_i2c(debug=debug)

            for addr, in_use in i2c_addresses:
                if in_use:
                    device_name, device_driver = self.lookup(addr, debug=debug)
                    self._devices.append([addr, device_name, device_driver, in_use])
                else:
                    logging.info(f"CFG:\tKein Gerät an der Adresse {addr}")
        except Exception as ex:
            logging.exception("CFG:\tFehler beim Scannen der I2C-Geräte: %s", ex)
            self.set_dummy_devices()

        try:
            from sensor.udp_daten2 import OPENCPN_Sensor
            self.udp_sensor = OPENCPN_Sensor()
        except Exception as ex:
            logging.info("CFG:\tUDP-Support nicht verfügbar - %s" % ex)

        try:
            from sensor.compass import compass_Sensor
            self.compass_sensor = compass_Sensor()
        except Exception as ex:
            logging.info("CFG:\tcompass-Support nicht verfügbar - %s" % ex)

            
    def scan_i2c(self, debug=False):
        """ Scannt den I2C-Bus und gibt eine Liste von erkannten Geräten zurück. """
        try:
            import raspberrypi

            # Führe den I2C-Scan durch
            proc = subprocess.Popen(['sudo', 'i2cdetect', '-y', '1'],
                                     stdout=subprocess.PIPE,
                                     close_fds=True)
            std_out_txt, std_err_txt = proc.communicate()
            std_out_txt = std_out_txt.decode('utf-8')

            if debug:
                logging.debug("I2C-Scan-Ausgabe:")
                logging.debug(std_out_txt)

            addr = []
            lines = std_out_txt.rstrip().split("\n")

            if "command not found" in std_out_txt:
                raise RuntimeError("Das 'i2cdetect'-Kommando ist nicht verfügbar. Bitte installieren oder sicherstellen, dass es im PATH ist.")

            for i in range(1, len(lines)):  # Zeilen ab der zweiten verarbeiten
                row = lines[i].strip()
                if debug:
                    logging.debug(f"Verarbeite Zeile {i}: {row}")
                for j in range(16):  # Maximal 16 Spalten pro Zeile
                    idx_j = j * 3 + 4
                    if idx_j + 2 <= len(row):  # Nur gültige Indizes verwenden
                        cell = row[idx_j:idx_j + 2].strip()
                        if cell and cell != "--":
                            hexAddr = 16 * (i - 1) + j
                            logging.info("    ...Gerät an Adresse: %s %s", hex(hexAddr), cell)
                            addr.append([hexAddr, cell == "UU"])
                    else:
                        if debug:
                            logging.debug(f"Ungültiger Index: idx_i={i}, idx_j={idx_j} (Zeilenlänge: {len(row)})")
            return addr

        except Exception as e:
            logging.error(f"Fehler beim Scannen der I2C-Geräte: {e}")
            return []



    def set_dummy_devices(self):
        logging.info("CFG:\tSetze Dummy-Geräte ein.")
        self.drive_controller = DummyDriveController()
        self.ruder_sensor = None
        self.compass_sensor = None
        self.tasten_sensor = None
        self.udp_sensor = None

    def lookup(self, addr, debug=False):
        if(debug):
            logging.debug("CFG:\tChecking for driver for device at i2c %s" % addr)

        import raspberrypi
        from smbus import SMBus
        # In configure_devices oder lookup:
        shared_i2c_bus = SMBus(1)  # Einmalig erzeugen und weitergeben
        
        if addr == 0x20:
            try:
                from sensor.Tasten import TASTEN_Sensor
                self.tasten_sensor = TASTEN_Sensor(i2c_bus=shared_i2c_bus, debug=debug)
            except Exception as ex:
                logging.warning("CFG:\tError setting up Tasten over i2c - %s" % ex)
            return "Tasten", self.tasten_sensor

        if addr == 0x21:  # Adresse für den Drive_Controller
            try:
                from vehicle.drive_controller import Drive_Controller
                self.drive_controller = Drive_Controller(i2c_bus=shared_i2c_bus, debug=debug)
                logging.info("DriveController erfolgreich initialisiert.")
                return "Drive", self.drive_controller
            except Exception as e:
                logging.error(f"Fehler bei der Initialisierung des DriveControllers: {e}")
                self.drive_controller = DummyDriveController()
                return "Drive", self.drive_controller


        elif addr == 0x68:
            try:
                from sensor.ruderlage import ruderlage_Sensor
                self.ruder_sensor = ruderlage_Sensor(i2c_bus=shared_i2c_bus, debug=debug)
            except Exception as ex:
                logging.warning("CFG:\tError setting up Ruderlage over i2c - %s" % ex)
            return "Ruderlage", self.ruder_sensor

        else:
            return "unknown", None

class DummyDriveController(object):
    acc_level = 1.0
    steering_angle = 0.0
    rudder_angle = 0.0

    def __init__(self):
        pass
    def set_ruder(self, observed_ruder):
        logging.debug("LOCAL:\truder set to: %s" % observed_ruder)
        self.observed_ruder = observed_ruder
        pass
    
    def set_steering(self, angle):
        logging.debug("LOCAL:\tSteering set to: %s" % angle)
        #logging.debug("LOCAL:\truder set to: %s" % set_ruder)
        self.steering_angle = 0
        #die obere Zeile habe ich gendert, sonst stand da nur = angle
        pass
    
    def halt(self):
        logging.debug("LOCAL:\tDrive halting.")
        self.throttle_level = 0.0
        self.steering_angle = 0.0
        pass

class VehicleConstants:
    def __init__(self):
        # Hier definierst du alle Konstanten als Attribute der Klasse
        self.gainp = 0.8
        self.gaini = 0.5
        self.gaind = 0.3
        self.max_response = 15
        self.dead_zone = 5
    
    def get(self, key, default=None):
        if hasattr(self, key):
            return getattr(self, key)
        return default
