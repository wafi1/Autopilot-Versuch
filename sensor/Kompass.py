import tkinter as tk
import serial
import threading
import time
import socket

SERIALDEVICE = '/dev/ttyUSB0'

port = "/dev/ttyUSB0"

KPK = ()
MW = ()
WE = ()


ser = serial.Serial(port, baudrate = 4800, timeout = 0.5)


UDP_IP = '0.0.0.0'
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def acquire_value():
    while True:
        line = ser.readline()
        line2 = line.decode('latin-1')
        if line2.startswith("$HCHDG"):
            KPK = line2.split(",")[1]
            KPK = float(KPK)
            MW = line2.split(",")[4]
            MW = float(MW)
            WE = line2.split(",")[5]
            if WE.startswith("W"):
                KPK = KPK + MW
            else:
                KPK = KPK - MW
            if KPK > 360:
                KPK = KPK -360
            elif KPK <0:
                KPK = 360 - KPK
            else:
                KPK = KPK
            #sock1 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            
            pot_value.set(KPK)
            ku = str(KPK).encode()
            sock.sendto(ku, (UDP_IP, UDP_PORT))
            
            

# Top level window
frame = tk.Tk()
frame.title("Kompasskurs [°]")
frame.geometry('800x400')
#frame.config(bg="red")

pot_value = tk.StringVar( frame)

PotValue = tk.Label(frame, width=10, height=10, textvariable=pot_value, borderwidth=3, relief="solid", bg="grey", fg='blue', font=("Tempus Sans ITC", 160,"bold"))
PotValue.pack()

lbl = tk.Label(frame, text = "Kurs")
lbl.pack()

acquire_thread = threading.Thread(target=acquire_value)
acquire_thread.start()

frame.mainloop()
