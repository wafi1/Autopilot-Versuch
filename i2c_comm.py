import smbus
import logging

# Dummy-Klasse, wenn I2C nicht verfügbar ist
class DummyI2CComm:
    def __init__(self, bus_num=1, addr=0x20):
        self.bus_num = bus_num
        self.addr = addr
        logging.warning(f"DUMMY I2C: Kein I2C-Bus verfügbar. Simulation läuft.")
    
    def initialize(self):
        """Dummy-Methode, keine wirkliche Initialisierung."""
        logging.debug("DUMMY I2C: Initialisierung übersprungen.")
    
    def write_data(self, iodira, gpioa):
        """Dummy-Methode, keine wirkliche Kommunikation."""
        logging.debug(f"DUMMY I2C: Schreibe Daten {hex(iodira)} und {hex(gpioa)} (simuliert).")
    
    def read_data(self, register):
        """Dummy-Methode, gibt einen festen Wert zurück."""
        logging.debug(f"DUMMY I2C: Lese Daten von Register {hex(register)} (simuliert).")
        return 0xFF  # Dummy-Wert (kann angepasst werden)
    

class I2CComm:
    """Klasse zur Verwaltung der I2C-Kommunikation."""

    def __init__(self, bus_num=1, addr=0x20):
        """Initialisiert die I2C-Kommunikation mit einem bestimmten Bus und einer Adresse."""
        self.bus_num = bus_num
        self.addr = addr

        try:
            # Versuche, den echten I2C-Bus zu initialisieren
            self.i2cBus = smbus.SMBus(self.bus_num)
            logging.debug(f"I2C: I2C-Bus {self.bus_num} erfolgreich initialisiert.")
        except FileNotFoundError:
            # Wenn der I2C-Bus nicht verfügbar ist (z. B. auf einem PC ohne I2C-Hardware)
            logging.warning(f"I2C: Kein I2C-Bus gefunden, wechsle zu Dummy-Modus.")
            self.i2cBus = DummyI2CComm(self.bus_num, self.addr)

    def initialize(self):
        """Initialisiert das I2C-Gerät (z. B. Port A auf Ausgang setzen)."""
        try:
            if isinstance(self.i2cBus, DummyI2CComm):
                self.i2cBus.initialize()  # Dummy-Initialisierung
            else:
                self.i2cBus.write_byte_data(self.addr, 0x00, 0x00)  # Set Port A to output
                logging.debug(f"I2C: Port A des Geräts {hex(self.addr)} wurde als Ausgang gesetzt.")
        except Exception as e:
            logging.error(f"I2C: Fehler beim Initialisieren des I2C-Geräts {hex(self.addr)}: {e}")
    
    def write_data(self, iodira, gpioa):
        """Schreibt Daten auf den I2C-Bus."""
        try:
            if isinstance(self.i2cBus, DummyI2CComm):
                self.i2cBus.write_data(iodira, gpioa)  # Dummy-Schreiben
            else:
                self.i2cBus.write_byte_data(self.addr, iodira, gpioa)
                logging.debug(f"I2C: Geschriebene Daten auf {hex(self.addr)}: IODIRA={hex(iodira)}, GPIOA={hex(gpioa)}")
        except Exception as e:
            logging.error(f"I2C: Fehler beim Schreiben von Daten auf {hex(self.addr)}: {e}")
    
    def read_data(self, register):
        """Liest Daten von einem I2C-Gerät."""
        try:
            if isinstance(self.i2cBus, DummyI2CComm):
                return self.i2cBus.read_data(register)  # Dummy-Lesen
            else:
                data = self.i2cBus.read_byte_data(self.addr, register)
                logging.debug(f"I2C: Gelesene Daten von {hex(self.addr)}: Register={hex(register)}, Wert={hex(data)}")
                return data
        except Exception as e:
            logging.error(f"I2C: Fehler beim Lesen von Daten von {hex(self.addr)}: {e}")
            return None
