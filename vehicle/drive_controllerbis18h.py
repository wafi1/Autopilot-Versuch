import time
import logging
import smbus

PWM_CMD = 1  # Befehl für PWM und Richtung

class Drive_Controller:
    def __init__(self, address=0x21, i2c_bus=None, debug=False):
        self.debug = debug
        self.controller_address = address
        self.i2c_bus = i2c_bus or smbus.SMBus(1)
        self.max_speed = 6.8
        self.current_command = None  # Aktuell ausgeführter Befehl
        self.is_executing = False  # Status des Controllers (ob ein Befehl ausgeführt wird)

        logging.debug("Drive_Controller erfolgreich initialisiert.")

    def calculate_pulse_duration(self, speed):
        """
        Berechnet die Dauer des Steuerimpulses basierend auf der Geschwindigkeit.
        """
        if speed <= 0:
            return 0
        normalized_speed = max(0, min(speed / self.max_speed, 1))  # Normierung auf [0, 1]
        pulse_duration = 2 - (1.5 * normalized_speed)  # Dauer zwischen 2 und 0.5 Sekunden
        return pulse_duration

    def send_command(self, pwm_value, direction):
        """
        Sendet den Steuerbefehl an den Arduino über I2C.
        """
        try:
            self.i2c_bus.write_i2c_block_data(self.controller_address, PWM_CMD, [pwm_value, direction])
            logging.debug(f"Drive_Controller: Command sent: PWM={pwm_value}, Direction={direction}")
        except Exception as e:
            logging.error(f"Drive_Controller: Fehler beim Senden des Befehls: {e}")

    def control_ruder(self, final_steering, speed, angle_const=0):
        """
        Führt den Steuerbefehl aus. Überschreibt den alten Befehl, falls einer aktiv ist.
        """
        # Effektiver Steuerwinkel
        effective_angle = final_steering + angle_const
        logging.debug(f"Drive_Controller: Steuerbefehl erhalten - Angle={effective_angle}, Speed={speed}")

        # Überschreibe den aktuellen Befehl
        self.current_command = (effective_angle, speed, angle_const)
        if not self.is_executing:
            self._execute_command()

    def _execute_command(self):
        """
        Führt den aktuellen Befehl aus.
        """
        if self.current_command is None:
            return

        self.is_executing = True
        effective_angle, speed, angle_const = self.current_command

        try:
            # Rückstellung auf angle_const
            if angle_const != 0:
                self._apply_steering(-angle_const, speed)

            # Effektiven Winkel einstellen
            self._apply_steering(effective_angle, speed)

            # Rückstellung auf angle_const
            if angle_const != 0:
                self._apply_steering(angle_const, speed)

        except Exception as e:
            logging.error(f"Drive_Controller: Fehler während der Ausführung: {e}")
        finally:
            self.is_executing = False
            self.current_command = None  # Befehl abgeschlossen
            logging.debug("Drive_Controller: Befehl abgeschlossen.")
            # Steuerung abgeschlossen
            self.ready_for_new_command = True
            if self.is_ready():
                logging.debug("Drive_Controller: Ready for the next command.")
        

    def _apply_steering(self, angle, speed):
        """
        Führt den Steuerbefehl mit PWM-Signal aus.
        """
        pwm_value = max(0, min(int(abs(angle) * 255 / 25), 255))
        direction = 1 if angle > 0 else 2
        pulse_duration = self.calculate_pulse_duration(speed)

        logging.debug(f"Drive_Controller: Applying steering: Angle={angle}, PWM={pwm_value}, Duration={pulse_duration}")
        self.send_command(pwm_value, direction)
        time.sleep(pulse_duration)
        self.send_command(0, 0)

    def halt(self):
        """
        Stoppt alle Aktionen und setzt den Controller zurück.
        """
        self.send_command(0, 0)
        self.current_command = None
        self.is_executing = False
        logging.info("Drive_Controller: Steuerung angehalten.")

    def is_ready(self):
        """Überprüft, ob der Drive_Controller einsatzbereit ist."""
        return self.i2c_bus is not None

  # Beispielnutzung
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    controller = Drive_Controller(debug=True)

    try:
        # Beispiel 1: Steuerbord + Vorhaltewinkel
        controller.control_ruder(final_steering=10, speed=3.0, angle_const=5)
        assert controller.is_ready(), "Controller not ready after first command."

        # Beispiel 2: Backbord + Vorhaltewinkel
        controller.control_ruder(final_steering=-15, speed=4.5, angle_const=-3)
        assert controller.is_ready(), "Controller not ready after second command."

        # Beispiel 3: Neutralstellung
        controller.control_ruder(final_steering=0, speed=0, angle_const=0)
        assert controller.is_ready(), "Controller not ready after third command."

    except KeyboardInterrupt:
        controller.halt()  
