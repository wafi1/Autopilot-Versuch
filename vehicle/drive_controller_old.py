import threading
import time
import logging
import smbus

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(threadName)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

PWM_CMD = 1  # Befehl für PWM und Richtung

class Drive_Controller:
    def __init__(self, address=0x21, i2c_bus=None, debug=False):
        self.debug = debug
        self.controller_address = address
        self.i2c_bus = i2c_bus or smbus.SMBus(1)
        self.max_speed = 6.8
        self.latest_command = None
        self.command_lock = threading.Lock()
        self.running = True
        self.command_available = threading.Event()

        # Startet den Controller-Thread
        self.thread = threading.Thread(target=self._run, name="DriveControllerThread")
        self.thread.start()
        logging.debug("Drive_Controller-Thread wurde gestartet.")

    def calculate_pulse_duration(self, speed):
        if speed <= 0:
            return 0
        normalized_speed = max(0, min(speed / self.max_speed, 1))
        return 2 - (1.5 * normalized_speed)

    def send_command(self, pwm_value, direction):
        try:
            self.i2c_bus.write_i2c_block_data(self.controller_address, PWM_CMD, [pwm_value, direction])
            logging.debug(f"Drive: Command sent: PWM={pwm_value}, Direction={direction}")
        except Exception as e:
            logging.error(f"Drive: Fehler beim Senden des Befehls: {e}")

    def control_ruder(self, final_steering, speed, angle_const=0):
        logging.debug(f"Drive_Controller: control_ruder aufgerufen mit Steering={final_steering}, Speed={speed}, Angle={angle_const}")
        with self.command_lock:
            self.latest_command = (final_steering, speed, angle_const)
            logging.debug(f"Drive_Controller: Neuer Befehl erhalten - {self.latest_command}")
        self.command_available.set()

    def _send_command_to_hardware(self, steering, speed, angle_const):
        pwm_value = max(0, min(int(abs(steering) * 255 / 25), 255))
        direction = 1 if steering > 0 else 2
        pulse_duration = self.calculate_pulse_duration(speed)

        logging.debug(f"Drive_Controller: PWM={pwm_value}, Direction={direction}, Pulse={pulse_duration}")
        self.send_command(pwm_value, direction)
        time.sleep(pulse_duration)
        self.send_command(0, 0)

    def _run(self):
        while self.running:
            logging.debug("Drive_Controller: Warte auf neues Kommando...")
            self.command_available.wait()
            logging.debug("Drive_Controller: Neues Kommando erkannt.")
            with self.command_lock:
                if self.latest_command:
                    try:
                        steering, speed, angle_const = self.latest_command
                        logging.debug(f"Drive_Controller: Processing command - Steering={steering}, Speed={speed}, Angle={angle_const}")
                        self._send_command_to_hardware(steering, speed, angle_const)
                    except Exception as e:
                        logging.error(f"Drive_Controller: Fehler bei der Verarbeitung des Befehls - {e}")
                    finally:
                        self.latest_command = None
            self.command_available.clear()
            logging.debug("Drive_Controller: Kommando abgearbeitet.")

    def halt(self):
        self.running = False
        self.command_available.set()
        self.thread.join()
        self.send_command(0, 0)
        logging.debug("Drive_Controller gestoppt.")

    def is_ready(self):
        with self.command_lock:
            return self.latest_command is None and self.running


if __name__ == "__main__":
    controller = Drive_Controller(debug=True)

    try:
        logging.debug("Hauptprogramm: Sende erstes Kommando an Drive_Controller.")
        controller.control_ruder(final_steering=10, speed=3.0, angle_const=5)
        time.sleep(1)
        logging.debug("Hauptprogramm: Sende zweites Kommando an Drive_Controller.")
        controller.control_ruder(final_steering=-15, speed=4.5, angle_const=-3)
        time.sleep(1)
        logging.debug("Hauptprogramm: Sende drittes Kommando an Drive_Controller.")
        controller.control_ruder(final_steering=0, speed=0, angle_const=0)
        time.sleep(5)
    except KeyboardInterrupt:
        logging.debug("Hauptprogramm: Stoppe Drive_Controller.")
        controller.halt()
