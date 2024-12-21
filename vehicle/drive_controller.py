import time
import logging
import smbus

# I2C-Adressen und Registerdefinitionen
PWM_ADDRESS = 0x21  # I2C-Adresse des Arduino
PWM_CMD = 1         # Befehl für PWM und Richtung

class YachtController:
    def __init__(self, addr=PWM_ADDRESS, i2c_bus=1):
        self.i2c_bus = smbus.SMBus(i2c_bus)
        self.addr = addr
        self.max_speed = 6.3  # Maximale Geschwindigkeit in Knoten

    def calculate_pulse_duration(self, speed):
        """
        Berechnet die Dauer des Steuerimpulses basierend auf der Geschwindigkeit.
        Je niedriger die Geschwindigkeit, desto länger der Impuls.
        """
        if speed <= 0:
            return 0
        normalized_speed = max(0, min(speed / self.max_speed, 1))  # Normiert auf [0, 1]
        return 2 - (1.5 * normalized_speed)  # Dauer zwischen 2 und 0.5 Sekunden

    def send_command(self, pwm_value, direction):
        """
        Sendet den Steuerbefehl an den Arduino über I2C.
        """
        try:
            self.i2c_bus.write_i2c_block_data(self.addr, PWM_CMD, [pwm_value, direction])
            logging.debug(f"Command sent: PWM={pwm_value}, Direction={direction}")
        except Exception as e:
            logging.error(f"Fehler beim Senden des Befehls: {e}")

    def control_rudder(self, angle, speed, angle_const=0):
        """
        Steuert das Ruder basierend auf dem gewünschten Winkel, der Geschwindigkeit und dem konstanten Vorhaltewinkel.
        Der Vorhaltewinkel (`angle_const`) verschiebt die Ausgangsposition des Ruders.
        """
        # Gesamter Winkel inklusive Vorhaltewinkel
        effective_angle = angle + angle_const
        logging.debug(f"Effective angle (angle + angle_const): {effective_angle}")

        # PWM-Wert berechnen basierend auf dem effektiven Winkel
        pwm_value = int(abs(effective_angle) * 255 / 25)  # Winkel normiert auf 0–255
        pwm_value = max(0, min(pwm_value, 255))

        # Richtung setzen (1 = Steuerbord, 2 = Backbord)
        direction = 1 if effective_angle > 0 else 2
        pulse_duration = self.calculate_pulse_duration(speed)

        # Steuerimpuls in die gewünschte Richtung senden
        self.send_command(pwm_value, direction)
        time.sleep(pulse_duration)

        # Ruder für 2 Sekunden halten
        time.sleep(2)

        # Rückstellen in die Ausgangslage (angle_const)
        opposite_angle = -angle  # Gegenwinkel für Rückstellung
        self._return_to_const_angle(opposite_angle, speed, angle_const)

    def _return_to_const_angle(self, angle, speed, angle_const):
        """
        Führt das Ruder von der aktuellen Lage zurück zum konstanten Vorhaltewinkel (angle_const).
        """
        effective_angle = angle + angle_const
        pwm_value = int(abs(effective_angle) * 255 / 25)  # PWM basierend auf dem Zielwinkel
        pwm_value = max(0, min(pwm_value, 255))

        # Richtung setzen für Rückstellung
        direction = 1 if effective_angle > 0 else 2
        pulse_duration = self.calculate_pulse_duration(speed)

        # Impuls senden
        self.send_command(pwm_value, direction)
        time.sleep(pulse_duration)

        # Rudersteuerung beenden
        self.send_command(0, 0)

    def halt(self):
        """
        Setzt alle Signale zurück und stoppt die Steuerung.
        """
        self.send_command(0, 0)
        logging.info("Steuerung angehalten.")

# Beispielnutzung
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    controller = YachtController()

    try:
        # Beispielsteuerung: Winkel, Geschwindigkeit und konstanter Vorhaltewinkel
        controller.control_rudder(angle=10, speed=3.0, angle_const=5)  # 10° Steuerbord + 5° Vorhaltewinkel
        controller.control_rudder(angle=-15, speed=4.5, angle_const=-3)  # 15° Backbord + (-3°) Vorhaltewinkel
    except KeyboardInterrupt:
        controller.halt()
