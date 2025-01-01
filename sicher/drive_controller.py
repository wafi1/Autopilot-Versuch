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
        Je niedriger die Geschwindigkeit, desto länger der Impuls.
        """
        if speed <= 0:
            return 0
        normalized_speed = max(0, min(speed / self.max_speed, 1))  # Normiert auf [0, 1]
        return 2 - (1.5 * normalized_speed)  # Dauer zwischen 2 und 0.5 Sekunden
        logging.debug(f"Drive: Speed received: speed={speed}")
        


    def set_steering(self, final_steering):
        """
        Set the rudder steering final_steering directly.
        """
        logging.debug(f"Drive: Sending final_steering value: {final_steering}")
        # Translate final_steering into PWM value and direction
        pwm_value = int(abs(final_steering) * 255 / 25)
        pwm_value = max(0, min(pwm_value, 255))
        direction = 1 if final_steering > 0 else 2
        logging.debug(f"Drive: final_steering received: final_steering={final_steering}, PWM={pwm_value}, Direction={direction}")
        

        self.send_command(pwm_value, direction)

    def send_command(self, pwm_value, direction):
        """
        Sendet den Steuerbefehl an den Arduino über I2C.
        """
        try:
            self.i2c_bus.write_i2c_block_data(self.controller_address, PWM_CMD, [pwm_value, direction])  # Verwende controller_address
            logging.debug(f"Drive: Command sent: PWM={pwm_value}, Direction={direction}")
        except Exception as e:
            logging.error(f"Drive: Fehler beim Senden des Befehls: {e}")

    def control_ruder(self, final_steering, speed, angle_const=0):
        """
        Steuert das Ruder basierend auf dem gewünschten Winkel, der Geschwindigkeit und dem konstanten Vorhaltewinkel.
        Der Vorhaltewinkel (`angle_const`) verschiebt die Ausgangsposition des Ruders.
        """
        # Gesamter Winkel inklusive Vorhaltewinkel
        effective_angle = final_steering + angle_const
        logging.debug(f"Drive: Effective angle (angle + angle_const): {effective_angle}")

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
        opposite_angle = -final_steering  # Gegenwinkel für Rückstellung
        self._return_to_const_angle(opposite_angle, speed, angle_const)

    def _return_to_const_angle(self, final_steering, speed, angle_const):
        """
        Führt das Ruder von der aktuellen Lage zurück zum konstanten Vorhaltewinkel (angle_const).
        """
        effective_angle = final_steering + angle_const
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
        logging.info("Drive: Steuerung angehalten.")

# Beispielnutzung
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    controller = Drive_Controller(debug=True)

    try:
        # Beispielsteuerung: Winkel, Geschwindigkeit und konstanter Vorhaltewinkel
        controller.control_ruder(final_steering=10, speed=3.0, angle_const=5)  # 10° Steuerbord + 5° Vorhaltewinkel
        controller.control_ruder(final_steering=-15, speed=4.5, angle_const=-3)  # 15° Backbord + (-3°) Vorhaltewinkel
        controller.set_steering(10)  # Test: Steuerbord
        controller.set_steering(-10)
        controller.control_ruder(final_steering=0, speed=0, angle_const=0) 

    except KeyboardInterrupt:
        controller.halt()
