import time
from drive_controller import Drive_Controller  # Ersetzen Sie den Modulnamen entsprechend

controller = Drive_Controller(debug=True)

try:
    controller.control_ruder(final_steering=10, speed=3.0, angle_const=5)
    time.sleep(1)
    controller.control_ruder(final_steering=-15, speed=4.5, angle_const=-3)
    time.sleep(1)
    controller.control_ruder(final_steering=0, speed=0, angle_const=0)
    time.sleep(5)
except KeyboardInterrupt:
    controller.halt()
