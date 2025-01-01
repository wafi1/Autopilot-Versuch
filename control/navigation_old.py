
import math
import logging
import threading
import time

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(threadName)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

class NavigationUnit:
    """ Coordinator between perception, navigation commands, and drive control. """

    def __init__(self, perception_unit, drive_controller, vehicle_constants):
        self._perception_unit = perception_unit
        self._drive_controller = drive_controller
        self._vehicle_constants = vehicle_constants

        if self._drive_controller is None:
            raise ValueError("Drive Controller darf nicht None sein!")

        # local components
        self._heading_ctrl = BasicPIDControl(
            vehicle_constants.gainp,
            vehicle_constants.gaini,
            vehicle_constants.gaind,
            vehicle_constants.dead_zone,
            vehicle_constants.max_response,
        )

        self._kalman_filter = KalmanFilter()
        self._enabled = False
        self._desired_heading = 0.0
        self._angle_const = 0.0  # Offset for consistent rudder adjustments

        self._latest_command = None
        self._command_lock = threading.Lock()

        # Start threads
        self._running = True
        self._command_thread = threading.Thread(target=self._send_commands)
        self._update_thread = threading.Thread(target=self._auto_update)
        self._command_thread.start()
        self._update_thread.start()

        logging.debug(f"Drive controller passed to NavigationUnit: {_drive_controller}")

    @property
    def auto_mode_enabled(self):
        return self._enabled

    @staticmethod
    def calculate_angle_difference(observed_heading, desired_heading):
        """Berechnet die kürzeste Differenz und Richtung zwischen zwei Winkeln (0–360°)."""
        diff = (desired_heading - observed_heading + 360) % 360
        direction = 1 if diff > 180 else 2  # 1 = Backbord, 2 = Steuerbord
        if diff > 180:
            diff -= 360  # Negative Werte für Drehrichtung Backbord
        return diff, direction

    def update(self):
        """Update drive output for new observations."""
        if not self._enabled:
            return

        # Sensor readings
        observed_heading = self._perception_unit.observed_heading
        if observed_heading is None:
            logging.warning("NAV: Observed heading is None. Skipping update.")
            return

        desired_heading = self._perception_unit.observed_navigation
        if desired_heading is None or not isinstance(desired_heading, (int, float)):
            logging.error(f"NAV: Invalid desired_heading: {desired_heading}")
            return

        speed = self._perception_unit.observed_speed() or 1.0  # Default speed for testing

        # Apply Kalman filter
        filtered_heading = self._kalman_filter.update(observed_heading)

        # Calculate shortest angle difference
        diff, direction = self.calculate_angle_difference(filtered_heading, desired_heading)

        # Check tolerance
        if abs(diff) < 2:
            logging.debug("NAV: Heading within tolerance, no adjustment needed.")
            return

        # PID controller update
        dt = 1  # Assuming 1-second intervals
        try:
            steering_adjustment = self._heading_ctrl.update(
                v_d=desired_heading, v_m=filtered_heading, dt=dt
            )
        except Exception as ex:
            logging.exception("Navigation: PID update error - %s", ex)
            return

        # Include angle_const
        final_steering = steering_adjustment + self._angle_const

        # Store latest command
        with self._command_lock:
            self._latest_command = (final_steering, speed, self._angle_const)
            logging.debug("NAV: Command prepared: %s", self._latest_command)

    def _send_commands(self):
        """Thread-Funktion zum Senden von Steuerbefehlen an den _drive_controller."""
        while self._running:
            try:
                if self._drive_controller.is_ready():
                    logging.debug("_drive_controller ist bereit für neue Befehle.")
                    with self._command_lock:
                        command = self._latest_command
                        self._latest_command = None

                    if command is not None:
                        final_steering, speed, angle_const = command
                        logging.debug(
                            f"_Drive_Controller: Command received - Steering: {final_steering}, "
                            f"Speed: {speed}, Angle Const: {angle_const}"
                        )
                        try:
                            self._drive_controller.control_ruder(
                            final_steering=final_steering,
                            speed=speed,
                            angle_const=self._angle_const  # Sicherstellen, dass das korrekte Attribut verwendet wird
                            )
                            logging.debug(f"NAV: Command sent: Steering={final_steering}, Speed={speed}")
                        except Exception as ex:
                            logging.exception(f"NAV: Error sending command - {ex}")
                        finally:
                            with self._command_lock:
                                if hasattr(self, "_latest_command"):
                                    self._latest_command = None  # Löschen, falls vorhanden
                                else:
                                    logging.warning("NAV: Attempted to clear _latest_command, but it does not exist.")

                    else:
                        time.sleep(0.01)
                else:
                    logging.debug("NAV: _Drive_Controller not ready. Waiting...")
                    time.sleep(0.01)

            except Exception as e:
                logging.exception(f"NAV: Unexpected error in _send_commands - {e}")
                time.sleep(0.1)

    def _auto_update(self):
        """Background thread to automatically call update."""
        while self._running:
            if self._enabled:
                try:
                    self.update()
                except Exception as e:
                    logging.exception(f"Error in auto-update thread: {e}")
            time.sleep(0.1)

    def update_angle_const(self, recent_adjustments):
        """ Update angle_const based on recent steering adjustments. """
        if not recent_adjustments:
            logging.warning("No recent adjustments provided for angle_const.")
            return
        avg_adjustment = sum(recent_adjustments) / len(recent_adjustments)
        self._angle_const = round(avg_adjustment)

    def set_heading(self, heading):
        """ Set desired heading to maintain. """
        if not isinstance(heading, (float, int)):
            raise ValueError("Heading must be a number.")
        logging.debug(f"Setting desired heading to: {heading}")
        self._desired_heading = heading
        self.start()

    def start(self):
        """ Enable navigation control. """
        self._enabled = True

    def stop(self):
        """ Disable navigation control and reset parameters. """
        self._enabled = False
        self._desired_heading = 0.0
        self._angle_const = 0.0
        self._running = False
        self._command_thread.join()
        self._update_thread.join()


class BasicPIDControl:
    """ Basic discrete PID controller for supplied gain. """

    def __init__(self, gainp=0.0, gaini=0.0, gaind=0.0, dead_zone=None, max_response=None):
        self.gainp = gainp
        self.gaini = gaini
        self.gaind = gaind
        self.dead_zone = dead_zone
        self.max_response = max_response
        self.integrated_error = 0.0
        self.last_error = 0.0

    def update(self, v_d, v_m, dt):
        error = v_d - v_m
        p = self.gainp * error

        self.integrated_error += error * dt
        i = self.gaini * self.integrated_error

        d_error = (error - self.last_error) / dt
        d = self.gaind * d_error
        self.last_error = error

        response = p + i + d

        if self.dead_zone and abs(response) < self.dead_zone:
            return 0.0

        if self.max_response and abs(response) > self.max_response:
            return math.copysign(self.max_response, response)

        return response


class KalmanFilter:
    """Simple 1D Kalman filter for smoothing heading data."""

    def __init__(self, process_variance=1e-5, measurement_variance=0.1, threshold=0.5):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.estimated_value = 0.0
        self.error_covariance = 1.0
        self.threshold = threshold  # Schwellwert für dynamische Anpassungen

    def set_parameters(self, process_variance=None, measurement_variance=None, threshold=None):
        """Dynamically adjust filter parameters."""
        if process_variance is not None:
            self.process_variance = process_variance
        if measurement_variance is not None:
            self.measurement_variance = measurement_variance
        if threshold is not None:
            self.threshold = threshold


    def update(self, measurement):
        # Dynamische Anpassung des Prozessrauschens
        if abs(measurement - self.estimated_value) > self.threshold:
            self.process_variance *= 1.5  # Erhöhe bei starken Abweichungen
        else:
            self.process_variance = max(1e-5, self.process_variance * 0.9)  # Reduziere bei Stabilität

        # Prediction update
        self.error_covariance += self.process_variance

        # Measurement update
        kalman_gain = self.error_covariance / (
            self.error_covariance + self.measurement_variance
        )
        self.estimated_value += kalman_gain * (measurement - self.estimated_value)
        self.error_covariance *= 1 - kalman_gain

        return self.estimated_value
