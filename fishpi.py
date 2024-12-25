import sys
import logging
import argparse
#import tkinter as tk

import ui.controller
from core_kernel import FishPiKernel
from localconfig import FishPiConfig

FISH_PI_VERSION = 0.2


class FishPiRunMode:
    Inactive = 'inactive'
    Local = 'local'
    Manual = 'manual'
    Remote = 'remote'
    Auto = 'auto'
    Modes = [Inactive, Local, Manual, Remote, Auto]


class FishPi:
    """ Entrypoint and setup class. """
    selected_mode = FishPiRunMode.Manual
    config = FishPiConfig()

    def __init__(self):
        # Configure argument parsing
        parser = argparse.ArgumentParser(description='FishPi - An autonomous drop in the ocean.')
        parser.add_argument("-m", "--mode", help="operational mode to run", choices=FishPiRunMode.Modes,
                            default=FishPiRunMode.Local, type=str)
        parser.add_argument("-d", "--debug", help="increase debugging information output", action='store_true')
        parser.add_argument("--version", action='version', version=f'%(prog)s {FISH_PI_VERSION}')
        parser.add_argument("-s", "--server", help="server for remote device", default="raspberrypi.local", type=str)

        # Parse command line arguments
        selected_args = parser.parse_args()
        self.selected_mode = selected_args.mode
        self.debug = selected_args.debug
        self.config.server_name = selected_args.server

        # Initialize logging configuration
        self.setup_logging()

        # Log initial information
        logging.info(f"FISHPI:\tInitializing FishPi (v{FISH_PI_VERSION})...")

    def setup_logging(self):
        """ Setup logging configuration. """
        log_level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    def self_check(self):
        """ Perform system self-checks. """
        logging.info("FISHPI:\tChecking last running state...")
        # TODO: Implement check for .lastState file
        # TODO: Check power levels, if insufficient initiate emergency beacon mode
        logging.info("FISHPI:\tChecking sufficient power...")

    def configure_devices(self):
        """ Configure I2C and other attached devices. """
        self.config.configure_devices(self.debug)

    def run(self):
        """ Runs selected FishPi mode."""
        logging.info(f"FISHPI:\tStarting FishPi in mode: {self.selected_mode}")

        mode_functions = {
            FishPiRunMode.Inactive: self.run_inactive,
            FishPiRunMode.Local: self.run_ui,
            FishPiRunMode.Manual: self.run_ui,
            FishPiRunMode.Remote: self.run_headless,
            FishPiRunMode.Auto: self.run_auto,
        }

        run_function = mode_functions.get(self.selected_mode, self.run_invalid_mode)
        return run_function()

    def run_inactive(self):
        """ Handle inactive mode. """
        logging.info("FISHPI:\tInactive mode set - exiting.")
        return 0

    def run_ui(self):
        """ Runs in UI mode. """
        # configure devices for UI mode
        self.configure_devices()
        
        # Create the kernel
        kernel = FishPiKernel(self.config, debug=self.debug)
        
        # Start UI
        logging.info("FISHPI:\tLaunching UI...")
        """ naechste Zeile gext, drei Zeilen zugefügt """
        ui.controller.run_main_view_tk(kernel) if self.selected_mode == FishPiRunMode.Local else ui.controller.run_main_view_wx(self.config)

    
        logging.info("FISHPI:\tProgram complete - exiting.")
        return 0

    def run_headless(self):
        """ Runs in headless (manual) mode. """
        # configure devices for headless mode
        self.configure_devices()

        # Create the kernel
        kernel = FishPiKernel(self.config, debug=self.debug)

        # List connected devices
        kernel.list_devices()

        # Waiting for commands...
        logging.info("FISHPI:\tWaiting for commands...")

        # Running internal webhost or other headless operations can be added here
        # import web.webhost
        # web.webhost.run_main_host(kernel, self.config.rpc_port)    

        logging.info("FISHPI:\tProgram complete - exiting.")
        return 0

    def run_auto(self):
        """ Runs in full auto mode. """
        self.configure_devices()

        # Create the kernel
        kernel = FishPiKernel(self.config, debug=self.debug)

        # List devices (or run auto scripts)
        kernel.list_devices()

        # Run autonomous scripts
        logging.info("FISHPI:\tRunning autonomous scripts...")
        # Add autonomous scripts here
        logging.info("FISHPI:\tNo autonomous scripts implemented - exiting.")
        
        return 0

    def run_invalid_mode(self):
        """ Handle invalid mode selection. """
        logging.error("FISHPI:\tInvalid mode selected! Exiting.")
        return 1
    
    def stop(self):
        self.stop_flag = True
        print("FishPi wird beendet...")


def main():
    """ Main entry point for the FishPi program. """
    fishPi = FishPi()
    fishPi.self_check()
    return fishPi.run()


if __name__ == "__main__":
    import tkinter as tk
    status = main()
    sys.exit(status)

    FishPi = FishPiApp()

    def on_exit():
        FishPi.stop()
        root.destroy()
        
    root = tk.Tk()
    root.title("FishPi Controller")

    
    exit_button = tk.Button(root, text="Beenden", command=on_exit)
    on_exit_button.pack(pady=20)

    root.mainloop()
