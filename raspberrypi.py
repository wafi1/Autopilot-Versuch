import os
import smbus
import subprocess
import socket

def board_ver():
    """Get the revision number of the board from /proc/cpuinfo."""
    try:
        out = subprocess.check_output(['cat', '/proc/cpuinfo']).decode('utf-8')
        # Extract the 'Revision' line from the output
        revision = next(line.split(':')[1].strip() for line in out.split('\n') if line.startswith('Revision'))
        return revision
    except Exception as ex:
        print(f"Error fetching board revision: {ex}")
        return None

def i2c_bus():
    """Return an SMBus object for I2C communication."""
    return smbus.SMBus(1)

def serial_bus():
    """Return the default serial bus path."""
    return "/dev/ttyUSB0"  # Or return "/dev/ttyAMA0" for alternative devices.

def serial_bus1():
    """Return an alternative serial bus path."""
    return "/dev/ttyUSB1"

def udp_bus(ip='0.0.0.0', port=10110):
    """Return a UDP socket bound to the specified IP and port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))  # Bind the socket if you plan to receive data
    return sock

def udp1_bus(ip='0.0.0.0', port=5005):
    """Return a UDP socket bound to a different IP and port."""
    sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock1.bind((ip, port))  # Bind to a different port if necessary
    return sock1
