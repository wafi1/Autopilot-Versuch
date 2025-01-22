import logging

class Perception_Unit:
    def __init__(self, vehicle_constants, data):
        """
        Initialisiert das PerceptionUnit mit den Fahrzeugkonstanten und Daten.
        :param vehicle_constants: Ein Objekt der Klasse VehicleConstants.
        :param data: Die Fahrzeugdaten.
        """
        self._vehicle_constants = vehicle_constants  # Speichert das Objekt der Klasse VehicleConstants
        
        # Zugriff auf die Attribute der Klasse VehicleConstants
        self._gainp = vehicle_constants.gainp
        self._gaini = vehicle_constants.gaini
        self._gaind = vehicle_constants.gaind
        self._max_response = self._vehicle_constants.max_response
        self._dead_zone = self._vehicle_constants.dead_zone

        self._observed_navigation = None
        self._observed_speed = None
        self._observed_heading = None
        self._observed_ruder = None
        
    def update_pid(self, gainp, gaini, gaind):
        """Diese Methode aktualisiert die PID-Werte in der PerceptionUnit."""
        self._gainp = gainp
        self._gaini = gaini
        self._gaind = gaind
        logging.debug(f"WORLD: Updated PID values: gainp={gainp}, gaini={gaini}, gaind={gaind}")
    
    def observed_speed(self):
        return self._observed_speed
    
    @property
    def observed_heading(self):
        return self._observed_heading
    
    @property
    def observed_ruder(self):
        return self._observed_ruder
    
    @property
    def observed_navigation(self):
        return self._observed_navigation

    def set_observed_navigation(self, value):
        if not isinstance(value, (int, float)):
            raise ValueError("WORLD: observed_navigation must be a number")
        logging.debug(f"WORLD: Setting observed_navigation to: {value}")
        self._observed_navigation = value
    
    def update(self, data):
        """ Update observed speed, heading, location from model and sensor data. """
        try:
            # Kompassdaten
            if data.has_compass:
                self._observed_heading = data.compass_heading

            # GPS-basierte Steuerung
            #if data.has_navigation:
            self._observed_heading = data.basic_steer  # Nutzt Steuerkurs von Navigation

            # Geschwindigkeit
            if data.has_udp:
                self._observed_speed = data.udp_speed

            # Ruderwinkel
            if data.has_ruder:
                self._observed_ruder = data.ruder_Winkel

            # Navigation Heading
            self.set_observed_navigation(data.navigation_heading)

            logging.debug(f"WORLD: Perception: Updated observed_heading={self._observed_heading}, "
                      f"WORLD: observed_navigation={self._observed_navigation}")

        except Exception as ex:
            logging.exception(f"WORLD: Perception: Fehler in update – {ex}")

