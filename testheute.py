import importlib
import sys
import logging
import os

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG)

# Modulpfade hinzufügen
sys.path.append('/home/pi/autopilot_py3/control')  # Pfad für navigation.py
sys.path.append('/home/pi/autopilot_py3/perception')  # Pfad für world.py

def validate_module(module_name):
    """
    Überprüft, ob ein Modul korrekt importiert werden kann.
    :param module_name: Der Name des Moduls.
    :return: Das Modulobjekt oder None bei Fehler.
    """
    try:
        module = importlib.import_module(module_name)
        logging.info(f"Modul '{module_name}' erfolgreich geladen.")
        return module
    except Exception as ex:
        logging.error(f"Fehler beim Laden von Modul '{module_name}': {ex}")
        logging.debug("Traceback:", exc_info=True)
        return None

def main():
    """
    Führt den Test der Module aus und startet navigation.py mit Dummy-Werten, falls möglich.
    """
    # Module prüfen
    navigation_module = validate_module("navigation")
    perception_module = validate_module("world")

    if not navigation_module or not perception_module:
        logging.error("Fehlerhafte Module, Navigation kann nicht gestartet werden.")
        return

    # Dummy-Initialisierung der Navigation
    try:
        vehicle_constants = type("VehicleConstants", (object,), {
            "gainp": 1.0, 
            "gaini": 0.0, 
            "gaind": 0.0, 
            "dead_zone": 0.1, 
            "max_response": 10.0
        })()

        perception_unit = perception_module.Perception_Unit(vehicle_constants, data=None)
        drive_controller = type("DriveController", (object,), {
            "is_ready": lambda: True, 
            "control_ruder": lambda x, y, z: logging.info(f"Steering: {x}, Speed: {y}, Angle_Const: {z}")
        })()

        navigation_unit = navigation_module.NavigationUnit(
            perception_unit=perception_unit,
            drive_controller=drive_controller,
            vehicle_constants=vehicle_constants
        )

        navigation_unit.start()
        logging.info("Navigation erfolgreich gestartet.")
        # Beispiel: Dummy-Werte setzen und Update ausführen
        perception_unit.set_observed_navigation(90.0)
        perception_unit._observed_heading = 45.0
        navigation_unit.update()
        logging.info("Navigation erfolgreich aktualisiert.")
    except Exception as ex:
        logging.error(f"Fehler beim Starten der Navigation: {ex}")
        logging.debug("Traceback:", exc_info=True)

if __name__ == "__main__":
    main()
