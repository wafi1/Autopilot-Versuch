import smbus
import logging
import sys
import os
import time
from raspberrypi import i2c_bus


class TASTEN_Sensor:
    
    #Variablen
    #  how long to wait when we're looking for a response
    
    def __init__(self, address=0x20, i2c_bus=None, debug=False):
        self.debug = debug
        self.ADDR = address  # Standardadresse für den MCP23008
        self.IODIRB = 0x00   # Register für I/O-Richtung (Port B)
        self.GPIOB = 0x09    # Register für I/O Manipulation von Port B (GPIO)

        # Überprüfen Sie, ob der i2c_bus korrekt übergeben wurde. Falls nicht, default auf Bus 1
        if i2c_bus is None:
            self.i2c_bus = smbus.SMBus(1)  # I2C-Bus 1 auf Raspberry Pi
        else:
            self.i2c_bus = i2c_bus

        try:
            # Versuche die Kommunikation zu testen, indem du das IODIRB-Register liest
            iodirb_value = self.i2c_bus.read_byte_data(self.ADDR, self.IODIRB)
            logging.debug(f"Erfolgreich IODIRB Register gelesen: {bin(iodirb_value)}")
        except Exception as e:
            logging.error(f"Fehler beim Initialisieren des Sensors: {str(e)}")
            raise

        # Historische Daten, um bei Fehlern zurückzugreifen
        self.olddata = None

        if self.debug:
            logging.debug(f"Sensor mit Adresse {hex(self.ADDR)} auf I2C-Bus {self.i2c_bus} initialisiert.")


    def read_sensor(self):
        data = 64
        try:
            data = self.i2c_bus.read_byte_data(self.ADDR, self.GPIOB)
            self.olddata = data
            #print "Tasten", data
            return data
        except:
            return self.olddata
            logging.exception("Tasten py:\tError in update loop (Tasten) - %s" % ex)

        
    
    
        

