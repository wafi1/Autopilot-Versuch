import math
import logging

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
        logging.debug(f"Drive controller passed to NavigationUnit: {drive_controller}")

    @property
    def auto_mode_enabled(self):
        return self._enabled
    
    @staticmethod
    def calculate_angle_difference(angle1, angle2):
        """Berechnet die kürzeste Differenz zwischen zwei Winkeln (0–360°)."""
        diff = (angle2 - angle1 + 180) % 360 - 180
        return diff if diff != -180 else 180


    def update(self):
 
        """ Update drive output for new observations. """
        if not self._enabled:
            return

        # Sensor readings
        observed_heading = self._perception_unit.observed_heading
        desired_heading = self._perception_unit.observed_navigation

        # Apply Kalman filter to observed heading
        filtered_heading = self._kalman_filter.update(observed_heading)

        # Calculate shortest angle difference
        error = self.calculate_angle_difference(filtered_heading, desired_heading)
        
        logging.debug(
            "NAV: Filtered Heading=%f, Desired Heading=%f, Error=%f",
            filtered_heading, desired_heading, error,
        )

        # Calculate PID response
        dt = 1  # Assuming 1-second update intervals
        try:
            steering_adjustment = self._heading_ctrl.update(
                v_d=desired_heading, v_m=filtered_heading, dt=dt
            )
        except Exception as ex:
            logging.exception("Navigation: PID update error - %s", ex)
            return

        # Include angle_const in steering adjustment
        final_steering = steering_adjustment + self._angle_const

        logging.debug("NAV: Final Steering Adjustment: %f", final_steering)

        # Check drive controller readiness
        if not self._drive_controller.is_ready():
            logging.warning("Drive Controller is not ready.")
            return

        # Send commands to the drive controller
        try:
            self._drive_controller.set_steering(final_steering)
            logging.debug("NAV: Steering command sent: %f", final_steering)
        except Exception as ex:
            logging.exception("Navigation: Drive controller update error - %s", ex)



    def update_angle_const(self, recent_adjustments):
        """ Update angle_const based on recent steering adjustments. """
        avg_adjustment = sum(recent_adjustments) / len(recent_adjustments)
        self._angle_const = round(avg_adjustment)

    def set_heading(self, heading):
        """ Set desired heading to maintain. """
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
    """ Simple 1D Kalman filter for smoothing heading data. """

    def __init__(self, process_variance=1e-5, measurement_variance=0.1):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.estimated_value = 0.0
        self.error_covariance = 1.0

    def update(self, measurement):
        # Prediction update
        self.error_covariance += self.process_variance

        # Measurement update
        kalman_gain = self.error_covariance / (
            self.error_covariance + self.measurement_variance
        )
        self.estimated_value += kalman_gain * (measurement - self.estimated_value)
        self.error_covariance *= 1 - kalman_gain

        return self.estimated_value
