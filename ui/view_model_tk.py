import logging
import math
import tkinter as tk


class MainViewController:
    """ Coordinator between UI and main control layers. """

    def __init__(self, kernel, view_model):
        self._kernel = kernel
        self.model = view_model

    def update(self):
        """ Updates view model from kernel. """
        logging.debug(f"Type of self.model.navigation_heading: {type(self.model.navigation_heading)}")

        # Kompassdaten
        try:
            self.model.compass_heading.set(self._kernel.data.compass_heading)
        except Exception as ex:
            logging.exception("VIEW:\tError in update loop (Kompassfehler) - %s" % ex)

        # Navigationsdaten
        try:
            self.model.navigation_heading.set(self._kernel.data.navigation_heading)
        except Exception as ex:
            logging.exception("Fehler beim Update von navigation_heading: %s", ex)

        # Auswahl zwischen GPS- und Kompasskurs
        try:
            self.model.basic_steer.set(self._kernel.data.basic_steer)
        except Exception as ex:
            logging.exception("Fehler beim Update von basic_steer: %s", ex)

        
        try:
            self.model.udp_speed.set(self._kernel.data.udp_speed)
        except Exception as ex:
            logging.exception("VIEW:\tError in update loop (Geschwindigkeit) - %s" % ex)

        # Weitere UDP-Daten
        try:
            self.model.udp_KPK.set(self._kernel.data.udp_KPK)
            self.model.udp_Dist.set(self._kernel.data.udp_Dist)
            self.model.udp_track.set(self._kernel.data.udp_track)
            self.model.basic_steer.set(self._kernel.data.basic_steer)
        except Exception as ex:
            logging.exception("VIEW:\tError in update loop (UDP-Daten) - %s" % ex)

        # Ruderwinkel
        try:
            # Keine Nachkommastellen für Ruderwinkel
            self.model.ruder_Winkel.set(int(self._kernel.data.ruder_Winkel))
        except Exception as ex:
            logging.exception("VIEW:\tError in update loop (Ruderwinkel) - %s" % ex)

        # Tasten
        try:
            self.model.tasten_tasten.set(self._kernel.data.tasten_tasten)
        except Exception as ex:
            logging.exception("VIEW:\tError in update loop (Tasten) - %s" % ex)

    def set_manual_mode(self):
        """ Stops navigation unit and current auto-pilot drive. """
        self._kernel.set_manual_mode()

    def set_auto_pilot_mode(self):
        """ Stops current manual drive and starts navigation unit. """
        self._kernel.set_auto_pilot_mode()

    def halt(self):
        """ Commands the NavigationUnit and Drive Control to Halt! """
        self._kernel.halt()
        self._kernel.set_pause_mode()

    def update_perception_unit(self, gainp, gaini, gaind):
        """ Übergibt die PID-Werte an den Kernel. """
        self._kernel.set_perception_unit(gainp, gaini, gaind)

    def exit_mode(self):
        """ Commands the NavigationUnit and Drive Control to Halt! """
        self._kernel.halt()
        self._kernel.set_exit_mode()

    @property
    def auto_mode_enabled(self):
        return self._kernel.auto_mode_enabled

    def manual_mode_enabled(self):
        return self._kernel.manual_mode_enabled

    def set_steering(self, angle):
        angle_in_rad = (float(angle) / 180.0) * math.pi
        angle_in_rad *= -1.0  # Adjustment for slider in opposite direction
        self._kernel.set_steering(angle_in_rad)

    def set_heading(self, heading):
        """ Commands the NavigationUnit to set and hold a given heading. """
        if not isinstance(heading, (int, float)):
            raise ValueError("Heading must be a number.")
        logging.debug(f"UI: Setting heading to {heading}")
        self._kernel.set_heading(heading)


class MainViewModel:
    """ UI Model containing bindable variables. """

    def __init__(self, root):
        # Kompassdaten
        self.compass_heading = tk.IntVar(master=root, value=0)
        self.basic_steer = tk.IntVar(master=root, value=0) 

        # UDP-Daten
        self.udp_KPK = tk.IntVar(master=root, value=0)
        self.udp_Dist = tk.DoubleVar(master=root, value=0.0)
        self.udp_speed = tk.DoubleVar(master=root, value=0.0)
        self.udp_track = tk.IntVar(master=root, value=0)

        # Ruderwinkel
        self.ruder_Winkel = tk.IntVar(master=root, value=0)

        # Navigationsdaten
        self.navigation_heading = tk.DoubleVar(master=root, value=0.0)

        # Sonstige Daten
        self.tasten_tasten = tk.DoubleVar(master=root, value=0.0)

