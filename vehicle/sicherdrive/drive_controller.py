import time
import logging
import smbus
#from raspberrypi import i2c_bus


PWM_CMD = 1         # Befehl für PWM und Richtung
speed = 5

class Drive_Controller:
    def __init__(self, address=0x21, i2c_bus=None, debug=False):
        self.debug = debug
        self.controller_address = address
        self.i2c_bus = i2c_bus

        try:
            self.i2c_bus = i2c_bus or smbus.SMBus(1)
            print(f"Drive_Controller erfolgreich mit Adresse {hex(address)} initialisiert.")
        except Exception as e:
            print(f"Fehler beim Initialisieren des Drive_Controllers: {e}")
            raise
        
        self.max_speed = 6.8
    

    def calculate_pulse_duration(self, speed):
        """
        Berechnet die Dauer des Steuerimpulses basierend auf der Geschwindigkeit.
        Höhere Geschwindigkeit = kürzere Pulsdauer.
        """
        if speed <= 0:
            return 0
        normalized_speed = max(0, min(speed / self.max_speed, 1))  # Normierung auf [0, 1]
        pulse_duration = 2 - (1.5 * normalized_speed)  # Dauer zwischen 2 und 0.5 Sekunden
        logging.debug(f"Drive: Calculated pulse_duration: {pulse_duration} for speed: {speed}")
        return pulse_duration

    def send_command(self, pwm_value, direction):
        """
        Sendet den Steuerbefehl an den Arduino über I2C.
        """
        logging.debug("Sending PWM Command: PWM=%d, Direction=%d", pwm_value, direction)
        try:
            self.i2c_bus.write_i2c_block_data(self.controller_address, PWM_CMD, [pwm_value, direction])  # Verwende controller_address
            logging.debug(f"Drive: Command sent: PWM={pwm_value}, Direction={direction}")
        except Exception as e:
            logging.error(f"Drive: Fehler beim Senden des Befehls: {e}")

            
    def control_ruder(self, final_steering, speed, angle_const=0):
        """
        Steuert das Ruder mit präziser Rückstellung auf den Vorhaltewinkel (angle_const).
        Die Dauer der Steuerung wird durch die Geschwindigkeit (pulse_duration) bestimmt.
        """
        effective_angle = final_steering + angle_const
        logging.debug(
            f"Drive: Starting control_ruder. Effective angle: {effective_angle}, "
            f"Speed: {speed}, Angle_const: {angle_const}"
        )

        # 1. Rückstellung auf angle_const, falls notwendig
        if angle_const != 0:
            logging.debug(f"Drive: Compensating for previous angle_const: {-angle_const}")
            self._apply_steering(-angle_const, speed)

        # 2. Anwenden des neuen Steuerbefehls
        self._apply_steering(effective_angle, speed)

        # 3. Rückstellung auf angle_const
        if angle_const != 0:
            logging.debug(f"Drive: Returning to angle_const: {angle_const}")
            self._apply_steering(angle_const, speed)

        # Steuerung abgeschlossen
        self.ready_for_new_command = True
        if self.is_ready():
            logging.debug("Drive_Controller: Ready for the next command.")



    def _apply_steering(self, effective_angle, speed):
        """
        Steuerbefehl anwenden, basierend auf Winkel und Geschwindigkeit.
        Die Dauer des Impulses (pulse_duration) bestimmt, wie weit sich das Ruder bewegt.
        """
        pwm_value = int(abs(effective_angle) * 255 / 25)  # PWM-Wert aus Winkel berechnen
        pwm_value = max(0, min(pwm_value, 255))  # Begrenzen auf [0, 255]

        direction = 1 if effective_angle > 0 else 2  # Richtung basierend auf Winkel

        # Berechne die Pulsdauer basierend auf Geschwindigkeit
        pulse_duration = self.calculate_pulse_duration(speed)
        logging.debug(
            "Drive: Applying steering. Angle: %f, PWM: %d, Direction: %d, Duration: %f",
            effective_angle, pwm_value, direction, pulse_duration
        )

        # Steuerimpuls senden
        self.send_command(pwm_value, direction)
        time.sleep(pulse_duration)  # Halte den Befehl für die berechnete Dauer aktiv

        # PWM deaktivieren
        self.send_command(0, 0)
        logging.debug("Drive: Command completed. PWM turned off.")




    def halt(self):
        """
        Setzt alle Signale zurück und stoppt die Steuerung.
        """
        self.send_command(0, 0)
        logging.info("Drive: Steuerung angehalten.")

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
