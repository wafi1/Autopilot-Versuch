import math
import logging

class NavigationUnit:
    """ Coordinator between perception, navigation commands, and drive control. """
    
    def __init__(self, perception_unit, drive_controller, vehicle_constants):
        self._perception_unit = perception_unit
        self._drive_controller = drive_controller
        self._vehicle_constants = vehicle_constants
        
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

    def update(self):
        """ Update drive output for new observations. """
        if not self._enabled:
            return

        # Sensor readings
        observed_heading = self._perception_unit.observed_heading
        observed_ruder = self._perception_unit.observed_ruder
        desired_heading = self._desired_heading

        # Apply Kalman filter to observed heading
        filtered_heading = self._kalman_filter.update(observed_heading)

        # Adjust for 360-degree wrapping
        if filtered_heading > 270 and desired_heading < 90:
            desired_heading += 360
        elif filtered_heading < 90 and desired_heading > 270:
            filtered_heading += 360

        logging.debug(
            "NAV: Filtered Heading vs Desired Heading: (%f) vs (%f)",
            filtered_heading, desired_heading,
        )

        # Calculate PID response
        dt = 1  # Assuming 1-second update intervals
        try:
            steering_adjustment = self._heading_ctrl.update(
                desired_heading, filtered_heading, dt
            )
        except Exception as ex:
            logging.exception("Navigation: PID update error - %s", ex)
            return

        # Include angle_const in steering adjustment
        final_steering = steering_adjustment + self._angle_const

        logging.debug(
            "NAV: Steering Adjustment (PID + angle_const): %f", final_steering
        )

        # Send commands to the drive controller
        try:
            self._drive_controller.set_steering(final_steering)
            logging.debug("NAV: Steering sent to Drive (PID + angle_const): %f", final_steering
        )
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
