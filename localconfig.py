import logging
import logging.handlers
import socket
import smbus
import os
import platform
import subprocess
import time
import RPi.GPIO as GPIO

class FishPiConfig(object):

    _devices = []
    _root_dir = os.path.join(os.getenv("HOME"), "fishpi")

    def __init__(self):
        # TODO setup logging (from config)
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        console = logging.StreamHandler()
        logger.addHandler(console)
        
        if os.path.exists(self.config_file):
            # TODO read any static config from file
            pass
        
        # create directories
        if not os.path.exists(self._root_dir):
            os.makedirs(self._root_dir)
        if not os.path.exists(self.navigation_data_path):
            os.makedirs(self.navigation_data_path)
        if not os.path.exists(self.logs_path):
            os.makedirs(self.logs_path)

        # add file logging
        log_file_stem = os.path.join(self.logs_path, 'fishpi_%s.log' % time.strftime('%Y%m%d_%H%M%S'))
        handler = logging.handlers.RotatingFileHandler(log_file_stem, backupCount=50)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # can force new file start if needed
        #handler.doRollover()
        
        # default attachments to None
        self.compass_sensor = None
        self.drive_controller = None
        self.udp_sensor = None
        self.ruder_sensor = None
        self.tasten_sensor = None
        self.show_wp = None
        self.show_wi = None
        self.show_wd = None
        
        # load vehicle constants
        self._vehicle_constants = VehicleConstants()
        pass
    
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
        """ Configured resources folder relative to code paths. """
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    #
    # device configuration section
    #
 
    @property
    def devices(self):
        """ Attached devices. """
        return self._devices


    def configure_devices(self, debug=False):
        """ Configures i2c devices when running in appropriate environment. """
        
        # Nur Geräte konfigurieren, wenn es sich um ein Linux-System handelt
        if not(platform.system() == "Linux"):
            logging.info("CFG:\tNicht auf einem Linux-Distro ausgeführt. I2C oder andere Geräte werden nicht konfiguriert.")
            self.set_dummy_devices()
            return
        

        try:
            logging.info("CFG:\tKonfiguration von I2C-Geräten wird durchgeführt...")
            i2c_addresses = self.scan_i2c(debug=debug)  # I2C-Scan durchführen

            # Durchsuche alle erkannten Geräteadressen
            for addr, in_use in i2c_addresses:
                if in_use:  # Gerät ist vorhanden
                    device_name, device_driver = self.lookup(addr, debug=debug)
                    self._devices.append([addr, device_name, device_driver, in_use])
                else:
                    logging.info(f"CFG:\tKein Gerät an der Adresse {addr}")
        except Exception as ex:
            logging.exception("CFG:\tFehler beim Scannen der I2C-Geräte: %s", ex)
            # Setze Dummy-Geräte im Falle eines Fehlers
            self.set_dummy_devices()

        # Versuche, den UDP-Sensor zu laden
        try:
            from sensor.udp_daten2 import OPENCPN_Sensor
            self.udp_sensor = OPENCPN_Sensor()
        except Exception as ex:
            logging.info("CFG:\tUDP-Support nicht verfügbar - %s" % ex)

        # Versuche, den compass-Sensor zu laden
        try:
            from sensor.compass import compass_Sensor
            self.compass_sensor = compass_Sensor()
        except Exception as ex:
            logging.info("CFG:\tcompass-Support nicht verfügbar - %s" % ex)



        # Falls I2C-Geräte nicht gefunden wurden, Dummy-Geräte verwenden
        if not self.drive_controller:
            self.drive_controller = DummyDriveController()

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
                logging.debug(std_out_txt)
                logging.debug(std_err_txt)

            addr = []
            lines = std_out_txt.rstrip().split("\n")

            if lines[0] in "command not found":
                raise RuntimeError("i2cdetect nicht gefunden")

            
            for i in range(0, 8):
                for j in range(0, 16):
                    idx_i = i + 1
                    idx_j = j * 3 + 4
        
                    if idx_i < len(lines) and idx_j < len(lines[idx_i]):
                        cell = lines[idx_i][idx_j:idx_j + 2].strip()
                        if cell and cell != "--":
                            logging.info("    ...Gerät an Adresse: %s %s", hex(16 * i + j), cell)
                            hexAddr = 16 * i + j
                            if cell == "UU":
                                addr.append([hexAddr, True])
                            else:
                                addr.append([hexAddr, False])
                else:
                    logging.warning(f"Ungültiger Index: idx_i={idx_i}, idx_j={idx_j} (Zeilenlänge: {len(lines)})")

            return addr

        except Exception as e:
            logging.error(f"Fehler beim Scannen der I2C-Geräte: {e}")
            logging.error(f"Standardausgabe des I2C-Scans: {std_out_txt}")
            return []

    def set_dummy_devices(self):
        """Initialisiert Dummy-Geräte, wenn keine echten Geräte verfügbar sind."""
        logging.info("CFG:\tSetze Dummy-Geräte ein.")
        # Verwende Dummy-Controller und Sensoren
        self.drive_controller = DummyDriveController()
        self.ruder_sensor = None
        self.compass_sensor = None
        self.tasten_sensor = None
        self.udp_sensor = None


    def lookup(self, addr, debug=False):
        """ lookup available device drivers by hex address,
            import and create driver class,
            setup particular devices so easily retrieved by consumers. """
        if(debug):
            logging.debug("CFG:\tChecking for driver for device at i2c %s" % addr)
        
 
        import raspberrypi
        # ************************
        if addr == 0x68:
            try:
                from sensor.ruderlage import ruderlage_Sensor
                self.ruder_sensor = ruderlage_Sensor(i2c_bus=1, debug=debug)
            except Exception as ex:
                logging.warning("CFG:\tError setting up Ruderlage over i2c - %s" % ex)
            return "Ruderlage", self.ruder_sensor


        #elif addr == 0x60:
        #    try:
         #       from sensor.compass_CMPS10 import Cmps10_Sensor
         #       self.compass_sensor = Cmps10_Sensor(i2c_bus=raspberrypi.i2c_bus(), debug=debug)
        #    except Exception as ex:
         #       logging.warning("CFG:\tError setting up COMPASS over i2c - %s" % ex)
        #    return "COMPASS", self.compass_sensor
        
        
        elif addr == 0x20:    
            try:
                from sensor.Tasten import TASTEN_Sensor
                self.tasten_sensor = TASTEN_Sensor(i2c_bus=1, debug=debug)
            except Exception as ex:
                logging.warning("CFG:\tError setting up Tasten over i2c - %s" % ex)
            return "Tasten", self.tasten_sensor

                    

        
        elif addr == 0x21: # or addr == 0x70:
            # DriveController (using Adafruit PWM board) (not sure what 0x70 address is for...)
            try:
                from vehicle.drive_controller import I2C_Master_v02
                # TODO pwm addresses from config?
                self.drive_controller = I2C_Master_v02()
            except Exception as ex:
                logging.info("CFG:\tError setting up DRIVECONTROLLER over i2c - %s" % ex)
                self.drive_controller = DummyDriveController()
            return "DRIVECONTROLLER", self.drive_controller
        
                
        else:
            return "unknown", None


class DummyCameraController(object):
    """ 'Dummy' camera controller that just logs. """
    
    def __init__(self, resources_folder):
        self.enabled = False
        from PIL import Image
        temp_image_path = os.path.join(resources_folder, 'camera.jpg')
        self._last_img = Image.open(temp_image_path)
    
    def capture_now(self):
        if self.enabled:
            logging.debug("CAM:\tCapture image.")
        pass
    
    @property
    def last_img(self):
        return self._last_img

class DummyDriveController(object):
    """ 'Dummy' drive controller that just logs. """
    
    # current state
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


        

