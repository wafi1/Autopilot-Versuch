

import logging
import math
import os
import tkinter

class MainViewController:
    """ Coordinator between UI and main control layers. """
    
    def __init__(self, kernel, view_model):
        self._kernel = kernel
        self.model = view_model
       
    
    def update(self):
        """ Updates view model from kernel. """
        # compass data
        try:
            self.model.compass_heading.set("{:.1f}".format(self._kernel.data.compass_heading))
        except Exception as ex:
            self._kernel.data.compass_heading = False
            logging.exception("VIEW:\tError in update loop (Kompassfehler) - %s" % ex) 
        #self.model.compass_roll.set("{:.2f}".format(self._kernel.data.compass_roll))
        
        # udp data
        try:
            #self.model.udp_KPK.set("147.0")
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
        # navigation data
        try:
            self.model.navigation_KPK.set("{:.2f}".format(self._kernel.data.navigation_heading))
        except Exception as ex:
            self._kernel.data.navigation_heading = False
            logging.exception("VIEW:\tError in update loop (keine Kompasskurs gesetzt) - %s" % ex)
            
         #tasten data "{:.1f}".format
        try:
            self.model.tasten_tasten.set(self._kernel.data.tasten_tasten)
        except Exception as ex:
            self._kernel.data.tasten_tasten = False
            logging.exception("VIEW:\tError in update loop (keine Tasten) - %s"% ex)
            
    #@property
    
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
        #logging.debug(f"View:\tgain parameter set to: {gainp}, {gaini}, {gaind}")

        self._kernel.set_perception_unit(gainp, gaini, gaind)
        #logging.debug(f"View:\tgain parameter set to: {gainp}, {gaini}, {gaind}")

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
        angle_in_rad = (float(angle)/180.0)*math.pi
        # adjustment for slider in opposite direction - TODO - move to drive controller
        angle_in_rad = angle_in_rad * -1.0
        self._kernel.set_steering(angle_in_rad)
    
    # Route Planning and Navigation
    
    def set_heading(self, heading):
        """ Commands the NavigationUnit to set and hold a given heading. """
        self._kernel.set_heading(float(heading))
    


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
        self.navigation_KPK = tkinter.DoubleVar(master=root, value=0.0)
        self.tasten_tasten = tkinter.DoubleVar(master=root, value=0.0)

        


