import logging
import math
import os
import tkinter as tk  # Verwendung von tkinter anstelle von Tkinter (für Python 3.x)

# Callback-Intervall in Millisekunden (optimiert von 25ms auf 5ms)
callback_interval = 5

def run_main_view_tk(kernel):
    """Startet die Haupt-UI-Ansicht basierend auf dem Tkinter-Framework."""
    # Tkinter-Imports werden hier zusammengefasst
    from ui.view_model_tk import MainViewController
    from ui.view_model_tk import MainViewModel
    from ui.main_view_tk import MainView
    
    # Initialisiere das UI-System
    root = tk.Tk()  # Verwendung von tkinter anstelle von Tkinter
    root.title("FishPi - Proof Of Concept Vehicle Control")
    root.minsize(800, 460)
    root.maxsize(800, 400)
    root.configure(bg="dark green")
    
    # Erstelle das ViewModel und den Controller
    view_model = MainViewModel(root)
    controller = MainViewController(kernel, view_model)
    
    # Erstelle die Ansicht
    view = MainView(root, controller)

    # Callback zum Kernel für Updates hinzufügen
    # Etwas längere Verzögerung beim ersten Callback, um dem UI Zeit zur Initialisierung zu geben
    root.after(5000, update_callback_tk, root, controller, view)

    # Starte die Tkinter-Anwendungsschleife
    root.mainloop()

def update_callback_tk(root, controller, view):
    """Callback, um Updates durchzuführen. Muss am Ende erneut registriert werden."""
    
    logging.debug("UI: Aktualisierung des ViewModels und Kernel...")
    
    try:
        # Update des Kernels
        controller._kernel.update()
        
        # Fordert den Controller auf, das ViewModel zu aktualisieren
        controller.update()


        
        # Hier könnte die View ebenfalls aktualisiert werden, falls nötig
        # (z.B. für die Anzeige von Bildern, falls diese dynamisch sind)
        # view.update_callback()
        
    except Exception as ex:
        logging.error(f"Fehler beim Update der UI-Komponenten: {ex}")

    # Registriere das Callback erneut nach dem angegebenen Intervall
    root.after(callback_interval, update_callback_tk, root, controller, view)
