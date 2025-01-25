import time
import random
import math
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from threading import Thread
import queue

# PID-Regler-Klasse
class PIDController:
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.previous_error = 0
        self.integral = 0

    def compute(self, setpoint, measurement, dt):
        error = setpoint - measurement
        self.integral += error * dt
        derivative = (error - self.previous_error) / dt if dt > 0 else 0

        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        self.previous_error = error
        return output

# Funktion zur Simulation der Sensordaten
def sensor_simulation(data_queue):
    setpoint = 0.0  # Zielwert der Ruderlage
    rudder_angle = 0.0  # Startwert der Ruderlage
    pid_controller = PIDController(kp=1.0, ki=0.1, kd=0.05)
    start_time = time.time()

    while True:
        current_time = time.time()
        dt = current_time - start_time
        start_time = current_time

        # Simulierte Ruderlage mit zufälligen Schwankungen
        rudder_angle += random.uniform(-1, 1) + math.sin(current_time * 0.5)

        # Simulierte Beschleunigungswerte
        ax = 0.5 * math.sin(current_time * 0.2)
        ay = 0.3 * math.cos(current_time * 0.3)
        az = 0.8 + 0.1 * random.uniform(-1, 1)

        # PID-Regelung
        pid_output = pid_controller.compute(setpoint, rudder_angle, dt)

        # Daten in die Queue packen
        data_queue.put((rudder_angle, setpoint, pid_output, ax, ay, az))

        time.sleep(0.1)

# Funktion für das Live-Plotting
def live_plot(data_queue):
    rudder_data, setpoint_data, pid_output_data = [], [], []
    ax_data, ay_data, az_data = [], [], []
    time_data = []

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle("Simulierte Ruderlage, PID-Ausgabe und Beschleunigungswerte")

    # Achse 1: Ruderlage und PID
    ax1.set_title("Ruderlage und PID-Ausgabe")
    ax1.set_xlabel("Zeit (s)")
    ax1.set_ylabel("Winkel (°) / PID-Wert")
    line_rudder, = ax1.plot([], [], label="Ruderlage (°)")
    line_setpoint, = ax1.plot([], [], label="Sollwert (°)", linestyle="--")
    line_pid, = ax1.plot([], [], label="PID-Ausgabe", linestyle=":")

    ax1.legend()

    # Achse 2: Beschleunigungswerte
    ax2.set_title("Beschleunigungswerte")
    ax2.set_xlabel("Zeit (s)")
    ax2.set_ylabel("Beschleunigung (g)")
    line_ax, = ax2.plot([], [], label="ax", color="r")
    line_ay, = ax2.plot([], [], label="ay", color="g")
    line_az, = ax2.plot([], [], label="az", color="b")

    ax2.legend()
    start_time = time.time()

    def update(frame):
        while not data_queue.empty():
            rudder_angle, setpoint, pid_output, ax, ay, az = data_queue.get()
            current_time = time.time() - start_time
            time_data.append(current_time)
            rudder_data.append(rudder_angle)
            setpoint_data.append(setpoint)
            pid_output_data.append(pid_output)
            ax_data.append(ax)
            ay_data.append(ay)
            az_data.append(az)

            if len(time_data) > 100:
                time_data.pop(0)
                rudder_data.pop(0)
                setpoint_data.pop(0)
                pid_output_data.pop(0)
                ax_data.pop(0)
                ay_data.pop(0)
                az_data.pop(0)

        # Aktualisiere die Achse 1
        line_rudder.set_data(time_data, rudder_data)
        line_setpoint.set_data(time_data, setpoint_data)
        line_pid.set_data(time_data, pid_output_data)
        ax1.set_xlim(max(0, time_data[0]), time_data[-1] if time_data else 10)
        ax1.set_ylim(-50, 50)

        # Aktualisiere die Achse 2
        line_ax.set_data(time_data, ax_data)
        line_ay.set_data(time_data, ay_data)
        line_az.set_data(time_data, az_data)
        ax2.set_xlim(max(0, time_data[0]), time_data[-1] if time_data else 10)
        ax2.set_ylim(-2, 2)

        return line_rudder, line_setpoint, line_pid, line_ax, line_ay, line_az

    ani = FuncAnimation(fig, update, interval=100)
    plt.tight_layout()
    plt.show()

# Hauptprogramm
def main():
    data_queue = queue.Queue()

    # Starte die Simulation der Sensordaten in einem separaten Thread
    sensor_thread = Thread(target=sensor_simulation, args=(data_queue,))
    sensor_thread.daemon = True
    sensor_thread.start()

    # Starte das Live-Plotting
    live_plot(data_queue)

if __name__ == "__main__":
    main()
