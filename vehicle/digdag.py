import time
import logging
import smbus
from threading import Lock


class DriveController:
    def __init__(self, address=0x21, i2c_bus=None, debug=False):
        self.debug = debug
        self.controller_address = address
        self.i2c_bus = i2c_bus or smbus.SMBus(1)
        self.command_lock = Lock()  # Sperre für parallele Befehle
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
        logging.debug("DriveController erfolgreich initialisiert.")

    def send_command(self, command_block):
        """
        Sendet ein Paket von Kommandos über I2C.
        :param command_block: Liste von Werten (z. B. [Direction, PWM])
        """
        try:
            self.i2c_bus.write_i2c_block_data(self.controller_address, 0, command_block)
            logging.debug(f"Command block sent: {command_block}")
        except Exception as e:
            logging.error(f"Error sending command block: {e}")


    def calculate_pulse_duration(self, speed):
        """
        Berechnet die Dauer des Steuerimpulses basierend auf der Geschwindigkeit.
        """
        if speed <= 0:
            return 0
        normalized_speed = max(0, min(speed / 6.3, 1))
        return 2 - (1.5 * normalized_speed)

    def calculate_pwm_value(self, angle):
        """
        Berechnet den PWM-Wert basierend auf dem Winkel.
        """
        return max(102, min(int(abs(angle) * 255 / 25), 255))  # Wertebereich: 100 bis 255


    def control_ruder(self, final_steering, speed, angle_const=0):
        with self.command_lock:  # Sperre während der Steuerung aktivieren
            logging.debug(f"Executing control_ruder with final_steering={final_steering}, speed={speed}, angle_const={angle_const}")

            # Steuerwinkel und zugehörige Werte berechnen
            effective_angle = final_steering + angle_const
            pwm_value = self.calculate_pwm_value(effective_angle)
            direction = 1 if effective_angle > 0 else 2  # 1: Backbord, 2: Steuerbord
            pulse_duration = self.calculate_pulse_duration(speed)

            # Hauptbewegung: Richtung setzen und PWM senden
            self.send_command([direction, pwm_value])  # Start: Richtung und PWM
            time.sleep(pulse_duration)

            # Beide Richtungen auf LOW setzen
            self.send_command([3, 9])  # Backbord LOW
            self.send_command([4, 9])  # Steuerbord LOW
            time.sleep(0.05)  # Sicherstellen, dass die H-Brücke zurückgesetzt wird

            # Rückstellung auf Vorhaltewinkel
            adjusted_angle = -final_steering + angle_const
            if adjusted_angle != 0:
                pwm_value_return = self.calculate_pwm_value(adjusted_angle)
                direction_return = 1 if adjusted_angle > 0 else 2
                pulse_duration_return = self.calculate_pulse_duration(speed)

                # Rückbewegung: Richtung setzen und PWM senden
                self.send_command([direction_return, pwm_value_return])
                time.sleep(pulse_duration_return)

                # Beide Richtungen erneut auf LOW setzen
                self.send_command([3, 9])  # Backbord LOW
                self.send_command([4, 9])  # Steuerbord LOW
                time.sleep(0.05)  # Sicherstellen, dass die H-Brücke zurückgesetzt wird

            logging.debug("Control_ruder completed.")
    

    def halt(self):
        """
        Stoppt alle Aktionen und setzt die Steuerung zurück.
        """
        xbPin, bbPin, pwmPin = 1, 2, 3  # Beispiel-Pin-Nummern
        with self.command_lock:  # Sperre sicherstellen
            self.send_command([3, 4])   # XBPin LOW
            self.send_command([9, 0])   # BBPin LOW
            logging.info("DriveController gestoppt.")

    def is_ready(self):
        """
        Überprüft, ob der DriveController bereit ist, neue Befehle anzunehmen.
        """
        return not self.command_lock.locked()


if __name__ == "__main__":
    controller = DriveController(debug=True)

    try:
        # Beispiel: Steuerbord mit Vorhaltewinkel
        controller.control_ruder(final_steering=10, speed=3.0, angle_const=5)
        time.sleep(1)

        # Beispiel: Backbord mit Vorhaltewinkel
        controller.control_ruder(final_steering=-15, speed=4.5, angle_const=-3)
        time.sleep(1)

        # Steuerung stoppen
        controller.halt()
    except KeyboardInterrupt:
        controller.halt()
