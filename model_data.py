class POCVModelData:
    """ Internal model containing FishPi POCV state. """

    def __init__(self):
        # Compass Data
        self.has_compass = False
        self.compass_heading = 0.0

        # UDP Data
        self.has_udp = False
        self.udp_KPK = 0.0
        self.udp_Dist = 0.0
        self.udp_speed = 0.0

        # PID Gains
        self.has_pid = False
        self.pid_gainp = 0.0
        self.pid_gaini = 0.0
        self.pid_gaind = 0.0
        
        # ruder
        self.has_ruder = False
        self.ruder_Winkel = 0.0
        self.ruder_k = 0.0

        # wind
        self.has_wind = False
        self.wind_Wian = 0.0
        self.wind_Wspeed = 0.0
        self.wind_Wanz = 0.0
        
        # gyro
        self.has_gyro = False
        
        # accelerometer
        self.has_accelerometer = False
        
        # temperature
        self.has_temperature = False
        self.temperature = 0.0

        # Navigation
        self.has_navigation = False
        self.navigation_heading = 0.0

        # Korrekturen
        self.has_mode = False
        self.mode = 0

        # Tasten
        self.has_tasten = False
        self.tasten_tasten = 0.0

