import logging
import math
import tkinter

class MainViewController:
    """ Coordinator between UI and main control layers. """
    
    def __init__(self, kernel, view_model):
        self._kernel = kernel
        self.model = view_model
    
    def update(self):
        """ Updates view model from kernel. """
        # Debugging für Typüberprüfung der View-Model-Attribute
        logging.debug(f"Type of self.model.navigation_heading: {type(self.model.navigation_heading)}")
        
        # compass data
        try:
            self.model.compass_heading.set("{:.2f}".format(self._kernel.data.compass_heading))
        except Exception as ex:
            self._kernel.data.compass_heading = False
            logging.exception("VIEW:\tError in update loop (Kompassfehler) - %s" % ex) 
        
        # navigation data
        try:
            navigation_heading = self._kernel.data.navigation_heading
            if callable(navigation_heading):
                raise ValueError("navigation_heading ist eine Funktion und kein Wert.")
            self.model.navigation_heading.set("{:.2f}".format(navigation_heading))
        except Exception as ex:
            logging.exception("Fehler beim Update von navigation_heading: %s", ex)



        # udp data
        try:
            self.model.udp_KPK.set("{:.1f}".format(self._kernel.data.udp_KPK))
            self.model.udp_Dist.set("{:.1f}".format(self._kernel.data.udp_Dist))
            self.model.udp_speed.set("{:.1f}".format(self._kernel.data.udp_speed))
        except Exception as ex:
            self._kernel.data.udp_KPK = False
            self._kernel.data.udp_Dist = False
            self._kernel.data.udp_speed = False
            logging.exception("VIEW:\tError in update loop (kein Wegepunkt) - %s" % ex) 

        # ruder data
        try:
            self.model.ruder_Winkel.set("{:.1f}".format(self._kernel.data.ruder_Winkel))
        except Exception as ex:
            self._kernel.data.ruder_Winkel = False
            logging.exception("VIEW:\tError in update loop (keine Ruderlagenanzeige) - %s" % ex)
            
        # tasten data
        try:
            self.model.tasten_tasten.set(self._kernel.data.tasten_tasten)
        except Exception as ex:
            self._kernel.data.tasten_tasten = False
            logging.exception("VIEW:\tError in update loop (keine Tasten) - %s" % ex)
    
    # Control modes (Manual, AutoPilot, Wind)
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
        angle_in_rad = angle_in_rad * -1.0  # Adjustment for slider in opposite direction
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
        # compass data
        self.compass_heading = tkinter.DoubleVar(master=root, value=0.0)

        # other data
        self.udp_KPK = tkinter.DoubleVar(master=root, value=0.0)
        self.udp_Dist = tkinter.DoubleVar(master=root, value=0.0)
        self.udp_speed = tkinter.DoubleVar(master=root, value=0.0)
        self.ruder_Winkel = tkinter.DoubleVar(master=root, value=0.0)
        self.navigation_heading = tkinter.DoubleVar(master=root, value=0.0)
        self.tasten_tasten = tkinter.DoubleVar(master=root, value=0.0)
