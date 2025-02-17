import smbus
import logging
from localconfig import FishPiConfig
from model_data import POCVModelData
from control.navigation import NavigationUnit
from perception.world import Perception_Unit


class FishPiKernel:
    """Koordinator zwischen verschiedenen Schichten im FishPi-System."""
    
    # I2C Konfiguration
    ADDR = 0x20    # MCP23017 I2C Adresse
    WUERFEL = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0xc0, 0x00, 0x0c, 0x07, 0x80]  # Würfelmuster

    def __init__(self, config, debug=False):
        """Initialisiert den FishPiKernel mit der bereitgestellten Konfiguration."""
        self.config = config
        self.debug = debug

        self.BUSNR   = 1      # I2C-Bus-Nummer
        self.ADDR    = 0x20   # MCP23017 I2C-Adresse
        self.IODIRA  = 0x00   # Register fuer I/O-Datenflussrichtung Port A
        self.GPIOA   = 0x09   # Register fuer I/O Manipulation von Port A
        self.kdaten  = 0
        self.WUERFEL = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0xc0, 0x00, 0x0c, 0x07, 0x80] # Wuerfel-Muster
        self.i2c_bus = smbus.SMBus(self.BUSNR) # I2C-Objekt instanziieren
        self.i2c_bus.write_byte_data(self.ADDR, self.IODIRA, 0x00) # Port A -> komplett Ausg 
        
        # Sensoren und Fahrzeugkomponenten initialisieren
        self._compass_sensor = config.compass_sensor
        self._udp_sensor = config.udp_sensor
        self._ruder_sensor = config.ruder_sensor
        self._tasten_sensor = config.tasten_sensor
        self._vehicle_constants = config.vehicle_constants
        self._drive_controller = config.drive_controller
        self.current_LED = 0
        self.basic_steer = 0
        self.LED1 = False
        self.LED2 = False
        self.LED3 = False

        # Datenklasse
        self.data = POCVModelData()
        
        # Unterstützende Einheiten
        self._perception_unit = Perception_Unit(self._vehicle_constants, self.data)
        self._navigation_unit = NavigationUnit(self._perception_unit, self._drive_controller, self._vehicle_constants)
        
    def update(self):
        """Haupt-Update-Schleife für Sensoren, Wahrnehmung und Steuerung."""
        self.read_sensors()
        self.ui_man()
        self.control_mode()
        #self.LED_mode()
        self._perception_unit.update(self.data)
        self._navigation_unit.update()


    def read_sensors(self):
        """Read data from all sensors and update model data."""
        sensor_methods = [
            ("UDP", self.read_udp),
            ("compass", self.read_compass),
            ("Ruder", self.read_ruder),
            ("Tasten", self.read_tasten)
        ]
        
        for sensor_name, method in sensor_methods:
            try:
                method()
            except Exception as ex:
                logging.exception(f"CORE:\tError in reading {sensor_name} sensor: {ex}")
    
    # Sensor reading methods
    def read_compass(self):
        try:
            (heading) = self._compass_sensor.read_sensor()
            self.data.compass_heading = float(round(heading))
            self.data.has_compass = True
            logging.debug(f"CORE:\tCompass heading set to: {self.data.compass_heading}")
        except Exception as ex:
            logging.error(f"CORE:\tCompass module failure: {ex}")

    def read_udp(self):
        try:
            (KPK, Dist, speed, track) = self._udp_sensor.read_sensor()
            self.data.udp_KPK = float(round(KPK))
            self.data.udp_Dist = float(round(Dist))
            self.data.udp_speed = float(round(speed))  # Assuming `speed` exists in `data`
            self.data.udp_track = float(round(track))
            self.data.has_udp = True
            logging.debug(f"CORE:\tUDP KPK: {self.data.udp_KPK}, Dist: {self.data.udp_Dist}, Speed: {self.data.udp_speed}, Track: {self.data.udp_track}")
        except Exception as ex:
            logging.error("CORE:\tUDP module failure")
            self.data.has_udp = False

    def read_ruder(self):
        try:
            # Ruderwinkel auslesen
            Winkel = self._ruder_sensor.read_sensor()
        
            # Verarbeitung der Ruderwinkel-Daten
            self.data.ruder_Winkel = Winkel * -1 - self.data.ruder_k
            if abs(Winkel) > 25:
                self.set_pause_mode()
            self.data.has_ruder = True
            logging.debug(f"CORE:\tRuder angle: {self.data.ruder_Winkel}")
        except Exception as ex:
            logging.error(f"CORE:\tRuder sensor failure: {ex}")
            self.data.has_ruder = False
    
            
    def read_tasten(self):
        try:
            # Tastenstatus auslesen
            tasten_status = self._tasten_sensor.read_sensor()
        
            # Verarbeitung der Tastenstatus-Daten
            self.data.tasten_status = tasten_status
            self.data.has_tasten = True
            logging.debug(f"CORE:\tTasten status: {self.data.tasten_status}")
        except Exception as ex:
            logging.error(f"CORE:\tTasten sensor failure: {ex}")
            self.data.has_tasten = False


    def ui_man(self):
        try:
            tast = self.data.tasten_tasten
            if tast == 0:
                return         
            if 'oldtast' not in self.__dict__:
                self.oldtast = tast  # initialisiere 'oldtast' beim ersten Aufruf
            if tast > 0 and self.oldtast != tast:
                self.oldtast = tast
            else:
                return
            if 10 < self.oldtast < 40:
                self.set_manual_mode()
                self.data.mode = 1
            elif self.oldtast > 100:
                self.set_pause_mode()
                self.data.mode = 4
            elif 40 < self.oldtast < 100:
                self.set_auto_pilot_mode()
                self.data.mode = 2

        except Exception as ex:
            logging.error("CORE:\tError in UI manual mode logic")
            logging.error(f"Tastenstatus (Rohwert): {self.data.tasten_tasten} (Dezimalwert), {bin(self.data.tasten_tasten)} (Binarwert)")


    def control_mode(self):
        """Control mode logic based on current mode."""
        
        try:
            # Manuelle Steuerung
            if self.data.mode == 1:  # Manual Mode
                self.data.basic_steer = self.data.compass_heading  # Nutzt Kompassdaten
                if not self.LED1:
                    self.current_LED = 1
                    self.LED_mode()
                    self.LED1 = True
                    self.LED2 = False
                    self.LED3 = False
                self.data.has_mode = True

            # Automatischer Steuerung
            elif self.data.mode == 2:  # Auto Mode           
                self.data.navigation_heading = self.data.udp_KPK  # GPS-basierter Kurs
                self.data.basic_steer = self.data.udp_track 
                if not self.LED2:
                    self.current_LED = 2
                    self.LED_mode()
                    self.LED1 = False
                    self.LED2 = True
                    self.LED3 = False
                self.data.has_mode = True
                

            # Standby-Modus
            elif self.data.mode == 4:  # Standby Mode
                if not self.LED3:
                    self.current_LED = 3
                    self.LED_mode()
                    self.LED1 = False
                    self.LED2 = False
                    self.LED3 = True
                pass
            # Debugging für gesetzte Werte
            logging.debug(f"Kernel: mode={self.data.mode}, basic_steer={self.data.basic_steer}, "
                          f"navigation_heading={self.data.navigation_heading}, current_LED={self.current_LED}")

        except Exception as ex:
            logging.exception(f"Kernel: Fehler in control_mode – {ex}")

    def LED_mode(self):
        """Aktualisiert die LEDs basierend auf dem aktuellen Modus."""
        if self.current_LED == 1:  # Manual Mode
            self.i2c_bus.write_byte_data(self.ADDR, self.IODIRA, self.WUERFEL[8])
            self.i2c_bus.write_byte_data(self.ADDR, self.GPIOA, self.WUERFEL[0])
            

        elif self.current_LED == 2:  # Auto Mode
            self.i2c_bus.write_byte_data(self.ADDR, self.IODIRA, self.WUERFEL[8])
            self.i2c_bus.write_byte_data(self.ADDR, self.GPIOA, self.WUERFEL[2])

        elif self.current_LED == 3:  # Standby Mode
            self.i2c_bus.write_byte_data(self.ADDR, self.IODIRA, self.WUERFEL[8])
            self.i2c_bus.write_byte_data(self.ADDR, self.GPIOA, self.WUERFEL[1])

        else:
            # Fallback: Alle LEDs aus
            self.i2c_bus.write_byte_data(self.ADDR, self.IODIRA, self.WUERFEL[8])
            self.i2c_bus.write_byte_data(self.ADDR, self.GPIOA, self.WUERFEL[8])


    def set_perception_unit(self, gainp, gaini, gaind):
        """Setzt die PID-Werte in der PerceptionUnit."""
        logging.debug(f"Kernel: PID Werte gesetzt - gainp: {gainp}, gaini: {gaini}, gaind: {gaind}")
        self._perception_unit.update_pid(gainp, gaini, gaind)
 
    # Control mode actions
    def set_manual_mode(self):
        """Activate manual mode."""
        self.data.mode = 1
        self.halt()
        self.data.navigation_heading = self.data.compass_heading
        self._navigation_unit.start()
        logging.debug(f"Kernel set manual mode: navigation Werte gesetzt: {self.data.navigation_heading}")

    def set_auto_pilot_mode(self):
        """Activate auto-pilot mode."""
        self.data.mode = 2
        self.halt()
        self._navigation_unit.start()
        logging.debug(f"Kernel set auto mode: navigation Werte gesetzt: {self.data.navigation_heading}")

    def set_pause_mode(self):
        """Activate pause mode."""
        self.data.mode = 4
        self.data.navigation_heading = 0
        self.halt()
        self.data.basic_steer = self.data.compass_heading  # Nutzt Kompassdaten
        self._navigation_unit.stop()


    def halt(self):
        """Stop all control systems."""
        self._navigation_unit.stop()
        self._drive_controller.halt()

    def exit_mode(self):
        logging.info("FISHPI:\tBeenden des Programms...")
        stop_threads()  # Stopp alle Hintergrund-Threads
        self.master.quit()  # Stoppt den Eventloop
        self.master.destroy()  # Zerstört das Fenster und alle Ressourcenself.master.destroy()  # Beendet das Programm über das übergebene root-Objekt
        
    def set_heading(self, heading):
        """ Commands the NavigationUnit to set and hold a given heading. """
        if not isinstance(heading, (int, float)):
            raise ValueError("Heading must be a number.")
        self._navigation_unit.set_heading(heading)
        logging.debug(f"Kernel set via UI: navigation heading set to: {heading}")

        
    @property
    def auto_mode_enabled(self):
        return self._navigation_unit.auto_mode_enabled
    
    
