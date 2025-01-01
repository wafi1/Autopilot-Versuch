import time
import logging
import smbus
from threading import Lock

PWM_CMD = 1  # Befehl für PWM und Richtung

class Drive_Controller:
    def __init__(self, address=0x21, i2c_bus=None, debug=False):
        self.debug = debug
        self.controller_address = address
        self.i2c_bus = i2c_bus or smbus.SMBus(1)
        self.max_speed = 6.8
        self.current_command = None  # Aktuell ausgeführter Befehl
        self.is_executing = False  # Status des Controllers (ob ein Befehl ausgeführt wird)
        self.command_lock = Lock()  # Sperre für Befehle
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
            time.sleep(0.2)
        except Exception as e:
            logging.error(f"Drive_Controller: Fehler beim Senden des Befehls: {e}")

    def control_ruder(self, final_steering, speed, angle_const=0):
        """
        Führt den Steuerbefehl aus. Überschreibt den alten Befehl, falls einer aktiv ist.
        """
        with self.command_lock:  # Sperrt die Ausführung
            if self.is_executing:
                logging.warning("Drive_Controller: Ignoring command, still executing.")
                return

            # Effektiver Steuerwinkel
            self.current_command = (final_steering + angle_const, speed, angle_const)
            self._execute_command()

            if not self.is_ready():
                logging.warning("Drive: Drive Controller not ready. Skipping command.")
                raise RuntimeError("Drive controller is not ready")
    def _execute_command(self):
        """
        Führt den aktuellen Steuerbefehl aus.
        """
        if self.current_command is None:
            return

        self.is_executing = True
        effective_angle, speed, angle_const = self.current_command

        try:
            # Bewegung in Richtung des effektiven Winkels
            logging.debug(f"Drive_Controller: Executing steering with angle={effective_angle}, angle_const={angle_const}")
            self._apply_steering(effective_angle, speed, angle_const)

            # Rückstellung erfolgt in _apply_steering
            logging.debug("Drive_Controller: Steering completed with angle_const adjustment.")
        except Exception as e:
            logging.error(f"Drive_Controller: Fehler während der Ausführung: {e}")
        finally:
            self.is_executing = False
            self.current_command = None  # Befehl abgeschlossen
            logging.debug("Drive_Controller: Befehl abgeschlossen.")


    def _apply_steering(self, angle, speed, angle_const=0):
        """
        Führt den Steuerbefehl aus und stellt anschließend auf angle_const zurück.
        """
        # Berechnung der PWM-Werte und Richtung für die Hauptbewegung
        pwm_value = max(0, min(int(abs(angle) * 255 / 25), 255))
        direction = 1 if angle > 0 else 2
        pulse_duration = self.calculate_pulse_duration(speed)

        # Hauptbewegung
        logging.debug(f"Drive_Controller: Steering in direction {direction}, PWM={pwm_value}, Duration={pulse_duration}")
        self.send_command(pwm_value, direction)
        time.sleep(pulse_duration)
        self.send_command(0, 0)  # Motor stoppen

        # Rückstellbewegung (symmetrisch oder auf angle_const)
        adjusted_angle = -angle + angle_const
        if adjusted_angle != 0:  # Rückstellung erforderlich
            pwm_value_return = max(0, min(int(abs(adjusted_angle) * 255 / 25), 255))
            direction_return = 1 if adjusted_angle > 0 else 2
            pulse_duration_return = self.calculate_pulse_duration(speed)

            logging.debug(
                f"Drive_Controller: Returning to angle_const in direction {direction_return}, "
                f"PWM={pwm_value_return}, Duration={pulse_duration_return}"
            )
            self.send_command(pwm_value_return, direction_return)
            time.sleep(pulse_duration_return)
            self.send_command(0, 0)  # Motor erneut stoppen



    def halt(self):
        """
        Stoppt alle Aktionen und setzt den Controller zurück.
        """
        with self.command_lock:
            self.send_command(0, 0)
            self.current_command = None
            self.is_executing = False
            logging.info("Drive_Controller: Steuerung angehalten.")

    def is_ready(self):
        """Prüft, ob der Drive_Controller einsatzbereit ist."""
        return not self.is_executing and self.i2c_bus is not None

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    controller = Drive_Controller(debug=True)

    try:
        # Beispiel 1: Steuerbord + Vorhaltewinkel
        controller.control_ruder(final_steering=10, speed=3.0, angle_const=5)
        time.sleep(1)  # Wartezeit zwischen Befehlen

        # Beispiel 2: Backbord + Vorhaltewinkel
        controller.control_ruder(final_steering=-15, speed=4.5, angle_const=-3)
        time.sleep(1)  # Wartezeit zwischen Befehlen

        # Beispiel 3: Neutralstellung
        controller.control_ruder(final_steering=0, speed=0, angle_const=0)

    except KeyboardInterrupt:
        controller.halt()
