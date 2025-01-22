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
from sensor.tasten import TASTEN_Sensor
from sensor.ruderlage import ruderlage_Sensor
from sensor.udp_daten2 import OPENCPN_Sensor
from sensor.compass import compass_Sensor

class FishPiConfig(object):
    _devices = []
    _root_dir = os.path.join(os.getenv("HOME"), "fishpi")

    def __init__(self):
        # Logger einrichten
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        console = logging.StreamHandler()
        logger.addHandler(console)

        if not os.path.exists(self._root_dir):
            os.makedirs(self._root_dir)

        log_file_stem = os.path.join(self._root_dir, 'fishpi_%s.log' % time.strftime('%Y%m%d_%H%M%S'))
        handler = logging.handlers.RotatingFileHandler(log_file_stem, backupCount=50)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        self.shared_i2c_bus = smbus.SMBus(1)
        self.tasten_sensor = None
        self.drive_controller = None
        self.ruder_sensor = None
        self.compass_sensor = None
        self.udp_sensor = None

        self._vehicle_constants = VehicleConstants()

    @property
    def vehicle_constants(self):
        return self._vehicle_constants

    def configure_devices(self, debug=False):
        try:
            logging.info("CFG:\tStarte Konfiguration der Geräte...")
            # Direkte Initialisierung der Geräte
            from vehicle.drive_controller import Drive_Controller
            self.drive_controller = Drive_Controller(i2c_bus=self.shared_i2c_bus, debug=debug)
        except Exception as ex:
            logging.error(f"CFG:\tFehler bei der Initialisierung des Drive_controllers: {ex}")
            self.drive_controller = None  # Fallback
     
        try:
            from sensor.tasten import TASTEN_Sensor
            self.tasten_sensor = TASTEN_Sensor(i2c_bus=self.shared_i2c_bus, debug=debug)
        except Exception as ex:
            logging.error(f"CFG:\tFehler bei der Initialisierung des Drive_controllers: {ex}")
            self.drive_controller = None  # Fallback
            
        # Ruder-Sensor initialisieren
        try:
            from sensor.ruderlage import ruderlage_Sensor
            self.ruder_sensor = ruderlage_Sensor(i2c_bus=self.shared_i2c_bus, debug=debug)
            logging.info("CFG:\tRuder-Sensor erfolgreich initialisiert.")
        except Exception as ex:
            logging.error(f"CFG:\tFehler bei der Initialisierung des Ruder-Sensors: {ex}")
            self.ruder_sensor = None  # Fallback

        # UDP-Sensor initialisieren
        try:
            from sensor.udp_daten2 import OPENCPN_Sensor
            self.udp_sensor = OPENCPN_Sensor()
            logging.info("CFG:\tUDP-Sensor erfolgreich initialisiert.")
        except Exception as ex:
            logging.error(f"CFG:\tFehler bei der Initialisierung des UDP-Sensors: {ex}")
            self.udp_sensor = None  # Fallback

        # Kompass-Sensor initialisieren
        try:
            from sensor.compass import compass_Sensor
            self.compass_sensor = compass_Sensor()
            logging.info("CFG:\tKompass-Sensor erfolgreich initialisiert.")
        except Exception as ex:
            logging.error(f"CFG:\tFehler bei der Initialisierung des Kompass-Sensors: {ex}")
            self.compass_sensor = None  # Fallback

            

    def set_dummy_devices(self):
        logging.info("CFG:\tSetze Dummy-Geräte ein.")
        self.drive_controller = DummyDriveController()
        self.tasten_sensor = None
        self.ruder_sensor = None
        self.compass_sensor = None
        self.udp_sensor = None

class DummyDriveController(object):
    def __init__(self):
        self.acc_level = 1.0
        self.steering_angle = 0.0
        self.rudder_angle = 0.0

    def set_ruder(self, observed_ruder):
        logging.debug(f"LOCAL:\truder set to: {observed_ruder}")
        self.rudder_angle = observed_ruder

    def set_steering(self, angle):
        logging.debug(f"LOCAL:\tSteering set to: {angle}")
        self.steering_angle = angle

    def halt(self):
        logging.debug("LOCAL:\tDrive halting.")
        self.acc_level = 0.0
        self.steering_angle = 0.0

class VehicleConstants:
    def __init__(self):
        self.gainp = 4.8
        self.gaini = 0.5
        self.gaind = 0.3
        self.max_response = 7
        self.dead_zone = 2

    def get(self, key, default=None):
        return getattr(self, key, default)
