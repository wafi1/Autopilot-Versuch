import logging
import threading
import time
import importlib
import sys
import os

sys.path.append('/home/pi/autopilot_py3/control')  # Pfad für navigation.py
sys.path.append('/home/pi/autopilot_py3/vehicle')  # Pfad für drive_controller.py


# Mock für den DriveController
class MockDriveController:
    def __init__(self):
        self.commands = []
        self.ready_state = True  # Simuliert den Zustand, dass der Controller bereit ist

    def is_ready(self):
        logging.debug("MockDriveController: Bereitschaft geprüft.")
        return self.ready_state

    def control_ruder(self, final_steering, speed, angle_const):
        logging.debug(
            f"MockDriveController: Empfange Befehl - Steering: {final_steering}, Speed: {speed}, Angle: {angle_const}"
        )
        self.commands.append((final_steering, speed, angle_const))

# Mock für die PerceptionUnit
class MockPerceptionUnit:
    def __init__(self, observed_heading, observed_navigation):
        self._observed_heading = observed_heading
        self._observed_navigation = observed_navigation

    @property
    def observed_heading(self):
        return self._observed_heading

    @property
    def observed_navigation(self):
        return self._observed_navigation

# Testprogramm
def test_navigation_to_drive_controller():
    logging.basicConfig(level=logging.DEBUG)

    # Erstellen der Mock-Objekte
    mock_drive_controller = MockDriveController()
    mock_perception_unit = MockPerceptionUnit(observed_heading=100.0, observed_navigation=110.0)

    # Erstellen einer NavigationUnit-Instanz
    from navigation import NavigationUnit  # Import der NavigationUnit
    vehicle_constants = type(
        "VehicleConstants", (object,), {"gainp": 1.0, "gaini": 0.1, "gaind": 0.05, "dead_zone": 2, "max_response": 30}
    )
    navigation_unit = NavigationUnit(mock_perception_unit, mock_drive_controller, vehicle_constants)

    # Aktivieren der Navigation und Setzen des Zielkurses
    navigation_unit.start()
    navigation_unit.set_heading(110.0)

    # Warten, um sicherzustellen, dass der Thread läuft
    time.sleep(2)

    # Navigation deaktivieren
    navigation_unit.stop()

    # Überprüfen der Ergebnisse
    if mock_drive_controller.commands:
        logging.info("Test erfolgreich: Befehle wurden an den DriveController gesendet.")
        for command in mock_drive_controller.commands:
            logging.info(f"Gesendeter Befehl: {command}")
    else:
        logging.error("Test fehlgeschlagen: Es wurden keine Befehle an den DriveController gesendet.")

if __name__ == "__main__":
    test_navigation_to_drive_controller()
