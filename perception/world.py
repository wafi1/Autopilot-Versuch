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

        self._observed_speed = 0.0
        self._observed_heading = 0.0
        self._observed_navigation = 0.0
        self._observed_ruder = 0.0
        self.update(data)
        
    def update_pid(self, gainp, gaini, gaind):
        """Diese Methode aktualisiert die PID-Werte in der PerceptionUnit."""
        self._gainp = gainp
        self._gaini = gaini
        self._gaind = gaind
        logging.debug(f"Updated PID values: gainp={gainp}, gaini={gaini}, gaind={gaind}")
    
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
        self._observed_navigation = value
    
    def update(self, data):
        """ Update observed speed, heading, location from model and sensor data. """

        if data.has_compass:
            compass_heading = data.compass_heading

        if data.has_udp:
            self._observed_speed = data.udp_speed

        if data.has_ruder:
            self._observed_ruder = data.ruder_Winkel
                
        # temp - use GPS speed
        if data.has_udp:
            self._observed_speed = data.udp_speed 

        # temp - average compass and GPS headings
        try:       
            if data.has_compass:
                self._observed_heading = compass_heading
        except Exception as ex:
            logging.exception("Navigation:\tError in update loop driver problem - %s" % ex)

        self.set_observed_navigation(data.navigation_heading)

        # Verwende die PID-Werte aus vehicle_constants (gainp, gaini, gaind)
       # logging.debug(f"Using PID constants: gainp={self._vehicle_constants.gainp}, gaini={self._vehicle_constants.gaini}, gaind={self._vehicle_constants.gaind}")
