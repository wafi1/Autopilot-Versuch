import logging
from tkinter import *
import tkinter.ttk as ttk
import sys
import threading
import os


class MainView(Frame, object):
    """ MainView class for POCV UI. """
    
    def __init__(self, master, view_controller):
        super(MainView, self).__init__(master, bd=1, relief=GROOVE)
        self.pack()
        self.create_widgets(master, view_controller)
        self._view_controller = view_controller
    
    def create_widgets(self, master, view_controller):
        """ Create widgets for view. """
        
        # top frame
        self.top_frame = Frame(master, bd=1, relief=GROOVE)
        self.top_frame.pack( fill=X)
        
        # map frame (in top sub-frame)
        self.map_frame = MapFrame(self.top_frame, view_controller)
        self.map_frame.pack(side=LEFT, fill=X, expand=True)
        

        
        # bottom sub-frame (in main frame)
        self.bottom_frame = Frame(master, bd=1, relief=GROOVE)
        self.bottom_frame.pack(fill=BOTH, expand=True)
        
        # info frame (in bottom sub-frame)
        self.info_frame = InfoFrame(self.bottom_frame, view_controller)
        self.info_frame.pack(side=LEFT, fill=BOTH, pady=5, expand=True)

        # controls frame (in bottom sub-frame)
        self.controls_frame = ControlsFrame(self.bottom_frame, view_controller)
        self.controls_frame.pack(side=LEFT, fill=BOTH, padx=2, pady=2, expand=False)


class MapFrame(Frame, object):
    """ UI Frame displaying map. """
    
    def __init__(self, master, view_controller):
        super(MapFrame, self).__init__(master, bd=1, relief=GROOVE)
        self._view_controller = view_controller
        


        # GPS heading info
        Label(self, text = "Kurs:", font=("Tempus Sans ITC", 30,"bold"), padx=5, pady=5, anchor=W, justify=LEFT).grid(row=1, sticky=W)
        Label(self, textvariable=view_controller.model.basic_steer, font=("Tempus Sans ITC", 30,"bold")).grid(row=1, column=1)
        Label(self, text = "Speed to waypoint:", font=("Tempus Sans ITC", 20,"bold"), padx=5,pady=5, anchor=W, justify=LEFT).grid(row=2, sticky=W)
        Label(self, textvariable=view_controller.model.udp_speed, font=("Tempus Sans ITC", 20,"bold")).grid(row=2, column=1)

 


class InfoFrame(Frame, object):
    """ UI Frame displaying information and status. """
    
    def __init__(self, master, view_controller):
        super(InfoFrame, self).__init__(master, bd=1, relief=SUNKEN)
        self._view_controller = view_controller

        Label(self, text = "Location Info:", pady=6, anchor=W, justify=LEFT).grid(row=0, columnspan=2, sticky=W)
        
 
        # compass heading info
        Label(self, text = "Compass Heading:", padx=3, anchor=W, justify=LEFT).grid(row=1, sticky=W)
        Label(self, textvariable=view_controller.model.compass_heading).grid(row=1, column=1)

        # UDP status        
        Label(self, text = "KPK to Waypoint:", padx=3, anchor=W, justify=LEFT).grid(row=5, sticky=W)
        Label(self, textvariable=view_controller.model.udp_KPK).grid(row=5, column=1)
        Label(self, text = "Distance to Waypoint:", padx=3, anchor=W, justify=LEFT).grid(row=6, sticky=W)
        Label(self, textvariable=view_controller.model.udp_Dist).grid(row=6, column=1)

        # Ruderwinkel
        Label(self, text = "Ruderwinkel    -=BB,      +=XB:", padx=3, anchor=W, justify=LEFT).grid(row=7, sticky=W)
        Label(self, textvariable=view_controller.model.ruder_Winkel).grid(row=7, column=1)

        # Navigation status
        Label(self, text = "Navigate :", padx=3, anchor=W, justify=LEFT).grid(row=8, sticky=W)
        Label(self, textvariable=view_controller.model.navigation_heading).grid(row=8, column=1)

        
        # Exit Button
        self.exit_button = Button(self, text="Exit", command=self.on_exit, height=2, width=10)
        self.exit_button.grid(row=12, columnspan=2, pady=10)  # Positioniere den Exit-Button


    def on_exit(self):
        """Beendet das Script."""
        print("Programm wird beendet...")

        root = self.winfo_toplevel()
        root.destroy()  # Beende die Hauptschleife
        
        

class ControlsFrame(Frame, object):
    """ UI Frame displaying controls for heading and throttle. """
    
    def __init__(self, master, view_controller):
        super(ControlsFrame, self).__init__(master, bd=1, relief=SUNKEN)
        self._view_controller = view_controller
        
        
        # top frame
        self.top_frame = Frame(self)
        self.top_frame.pack(fill=X)
        
        # Mode Buttons
        self.btn_pause = Button(self.top_frame, text="Standby", height=3, width=5, command=self.on_pause)
        self.btn_pause.config(relief=SUNKEN)
        self.btn_pause.pack(side=LEFT, padx=7, pady=10)
        
        self.btn_manual = Button(self.top_frame, text="Manual", height=3, width=5, command=self.on_set_manual_mode)
        self.btn_manual.config(relief=RAISED)
        self.btn_manual.pack(side=LEFT, padx=7, pady=10)        
        
        self.btn_auto = Button(self.top_frame, text="AutoPilot", height=3, width=5, command=self.on_set_auto_pilot_mode)
        self.btn_auto.config(relief=RAISED)
        self.btn_auto.pack(side=LEFT, padx=7, pady=10)

        # PID control sliders

        # Label und Slider für die PID-Werte (Proportional, Integral, Differential)
        self.p_label = Label(self, text="Kp (Proportional)", anchor=W)
        self.p_label.pack(padx=5, pady=5, anchor=W)

        self.gainp_slider = Scale(self, from_=0, to=10, orient=HORIZONTAL, resolution=0.5, showvalue=True, command=self.update_pid_values)
        self.gainp_slider.set(4.80)  # Standardwert Kp
        self.gainp_slider.pack(fill=X, padx=5, pady=5)

        self.i_label = Label(self, text="Ki (Integral)", anchor=W)
        self.i_label.pack(padx=5, pady=5, anchor=W)

        self.gaini_slider = Scale(self, from_=0, to=1, orient=HORIZONTAL, resolution=0.01, showvalue=True, command=self.update_pid_values)
        self.gaini_slider.set(0.55)  # Standardwert Ki
        self.gaini_slider.pack(fill=X, padx=5, pady=5)

        self.d_label = Label(self, text="Kd (Differential)", anchor=W)
        self.d_label.pack(padx=5, pady=5, anchor=W)

        self.gaind_slider = Scale(self, from_=0, to=0.05, orient=HORIZONTAL, resolution=0.001, showvalue=True, command=self.update_pid_values)
        self.gaind_slider.set(0.75)  # Standardwert Kd
        self.gaind_slider.pack(fill=X, padx=5, pady=5)

        # Anpassung der update_pid_values Methode
    def update_pid_values(self, value=None):
        """Diese Methode wird aufgerufen, wenn der Schieberegler bewegt wird."""
    
        # Hole die Werte aus allen drei Slidern
        gainp = self.gainp_slider.get()
        gaini = self.gaini_slider.get()
        gaind = self.gaind_slider.get()

        # Optional: Werten skalieren (hier durch Division mit 10)
        gainp = round(gainp / 10, 3)
        gaini = round(gaini / 10, 3)
        gaind = round(gaind / 10, 3)

        #logging.debug(f"PID Werte gesetzt: Kp={gainp:.3f}, Ki={gaini:.3f}, Kd={gaind:.3f}")

    
        # Update der PerceptionUnit mit den neuen PID-Werten
        self._view_controller.update_perception_unit(gainp, gaini, gaind)
        #logging.debug(f"PID Werte gesetzt: Kp={gainp}, Ki={gaini}, Kd={gaind}")

        
    def on_set_manual_mode(self):
        """ event handler for mode change """
        self.btn_auto.config(relief=RAISED)
        self.btn_pause.config(relief=RAISED)
        self.btn_manual.config(relief=SUNKEN)
        self._view_controller.set_manual_mode()

    def on_pause(self):
        """ event handler for mode change """
        self.btn_manual.config(relief=RAISED)
        self.btn_auto.config(relief=RAISED)
        self.btn_pause.config(relief=SUNKEN)
        self._view_controller.halt()
        
    def on_set_auto_pilot_mode(self):
        """ event handler for mode change """
        self.btn_pause.config(relief=RAISED)
        self.btn_manual.config(relief=RAISED)
        self.btn_auto.config(relief=SUNKEN)
        self._view_controller.set_auto_pilot_mode()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
    

