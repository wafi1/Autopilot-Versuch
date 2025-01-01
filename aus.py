import logging
import importlib

# Logging konfigurieren
logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")

# Module importieren
try:
    from perception.world import Perception_Unit
    from control.navigation import NavigationUnit
    from core_kernel import FishPiKernel
except ModuleNotFoundError as e:
    logging.error(f"Modul konnte nicht importiert werden: {e}")
    raise

# Liste der Module und zu testenden Attribute
modules_to_check = [
    {
        "module": Perception_Unit,
        "attributes": ["update_pid", "observed_navigation", "set_observed_navigation"],
    },
    {
        "module": NavigationUnit,
        "attributes": ["set_heading", "_desired_heading"],
    },
    {
        "module": FishPiKernel,
        "attributes": ["set_heading", "auto_mode_enabled"],
    },
]

# Module und Attribute überprüfen
for module_info in modules_to_check:
    module = module_info["module"]
    attributes = module_info["attributes"]

    for name in attributes:
        try:
            # Prüfen, ob das Attribut existiert
            if not hasattr(module, name):
                logging.error(f"Das Attribut '{name}' fehlt in {module.__name__}")
            else:
                logging.info(f"Attribut '{name}' erfolgreich in {module.__name__} gefunden.")
        except Exception as ex:
            logging.error(f"Fehler beim Zugriff auf '{name}' in {module.__name__}: {ex}")
