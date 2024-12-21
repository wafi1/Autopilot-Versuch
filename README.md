This autopilot is working together with, using a Raspberry Pi 3+ and 7` LCD :

- OpenCPN as navigation unit with GPS via NMEA 0183

- a potentiometer and a MCP 3426 as rudder indicator, connected with I2C

- compass type NASA clipper with NMEA 0183, connected to USB

- for buttons a MCP 23008 or 23017 port expander, connected with I2C_Master_v02

- as Motordriver a Arduino UNO to produce a PWM signal and a signal port/starboard rudder, to a H-bridge VNH 3 SP 30 and and old wheel autopilot using only mechanic and motor, NO connected by I2C

Short description:
3 modes:
    1. Standby
		2. Manual mode, actual compass heading will be desired heading
		3. automatic mode, desired heading will be send from OpenCPN following a route with waypoints
