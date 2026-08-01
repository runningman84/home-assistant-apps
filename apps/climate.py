"""ClimateControl app: manage HVAC devices and temperature modes based on presence, schedules and sensors.

Main features:
- Maintain different target temperatures for home, away, night, motion and vacation modes.
- Integrate external/outside temperature sensors to adjust behavior and enable summer mode.
- Respect opening sensors (windows/doors) and air-quality sensors (AQI, CO₂, VOC) to inhibit heating/cooling.
- React to motion, guest or vacation controls and to manual adjustments from GUI controls.
- Support per-mode control entities to change target temperatures via UI.

Key configuration keys (extracted from implementation):
- climate_controls: list of climate entity ids to manage (required).
- external_temperature_sensor / outside_temperature_sensor: optional sensor ids used for logic.
- home_temperature, night_temperature, away_temperature, vacation_temperature, motion_temperature: numeric targets for heating mode.
- home_temperature_cooling, night_temperature_cooling, etc.: numeric targets for cooling mode (defaults to cooling_temperature if not set).
- cooling_temperature: default cooling target (default: 22°C, used when status-specific cooling temperature not configured).
- *_hvac_mode: HVAC mode for heating (e.g., home_hvac_mode, default: 'heat').
- *_hvac_mode_cooling: HVAC mode for cooling (e.g., home_hvac_mode_cooling, default: 'cool').
- *_temperature_control: optional entity id (number/select) to change heating temperature via UI for that status.
- *_temperature_control_cooling: optional entity id (number/select) to change cooling temperature via UI for that status.
- min_temperature_heating, max_temperature_heating: temperature bounds for heating (default: 7°C - 30°C).
- min_temperature_cooling, max_temperature_cooling: temperature bounds for cooling (default: 16°C - 30°C).
- offset_temperature_heating, offset_temperature_cooling: static temperature offsets for calibration (default: 0°C).
- enable_pid: enable PID controller for dynamic temperature adjustment (default: false).
- pid_kp, pid_ki, pid_kd: PID controller gains (defaults: 1.0, 0.1, 0.05).
- pid_output_limit: maximum PID offset in °C (default: 5.0).
- aqi_sensor, voc_sensor, co2_sensor: optional air-quality sensors and thresholds (aqi_threshold, voc_threshold, co2_threshold).
- summer_temperature_threshold: threshold for summer detection (used for cooling activation logic).
- min_outside_temperature_for_cooling: minimum outside temperature required to enable cooling (default: 22°C).
- min_inside_temperature_for_cooling: minimum inside temperature required to enable cooling (default: 21°C).
- overdrive_mode, overdrive_heating_temperature, overdrive_cooling_temperature: aggressive heating/cooling targets.
- night_start, night_end, night_start_workday, night_end_workday: configurable night windows (in BaseApp defaults).

Example:
```yaml
climate_control:
    module: climate
    class: ClimateControl
    climate_controls:
        - climate.living_room
    opening_sensors:
        - binary_sensor.window_living
    # Heating temperatures for each status
    home_temperature: 21
    away_temperature: 17
    vacation_temperature: 15
    night_temperature: 18            # Optional: defaults shown in code
    motion_temperature: 21           # Optional: defaults shown in code
    # Cooling temperatures for each status (optional, falls back to cooling_temperature)
    home_temperature_cooling: 22     # Optional: cooling target for home status
    away_temperature_cooling: 24     # Optional: cooling target for away status
    night_temperature_cooling: 23    # Optional: cooling target for night status
    # Default cooling temperature (used when status-specific cooling temp not configured)
    cooling_temperature: 22          # Optional: default cooling target (default: 22°C)
    # Optional: HVAC modes for heating (default: 'heat')
    home_hvac_mode: heat
    away_hvac_mode: heat
    # Optional: HVAC modes for cooling (default: 'cool')
    home_hvac_mode_cooling: cool
    away_hvac_mode_cooling: off      # Turn off cooling when away to save energy
    # Optional: UI controls for heating temperatures
    home_temperature_control: input_number.climate_home_heating
    # Optional: UI controls for cooling temperatures
    home_temperature_control_cooling: input_number.climate_home_cooling
    min_temperature_heating: 7       # Optional: minimum for heating (default: 7°C)
    max_temperature_heating: 30      # Optional: maximum for heating (default: 30°C)
    min_temperature_cooling: 16      # Optional: minimum for cooling (default: 16°C)
    max_temperature_cooling: 30      # Optional: maximum for cooling (default: 30°C)
    offset_temperature_heating: -2   # Optional: calibration offset for heating (default: 0°C)
    offset_temperature_cooling: 0    # Optional: calibration offset for cooling (default: 0°C)
    # Optional: Enable PID controller for dynamic temperature adjustment (disabled by default)
    enable_pid: false                # Default: false - set to true to enable
    pid_kp: 1.0                      # Default: 1.0 - Proportional gain
    pid_ki: 0.1                      # Default: 0.1 - Integral gain
    pid_kd: 0.05                     # Default: 0.05 - Derivative gain
    pid_output_limit: 5.0            # Default: 5.0 - Maximum PID offset in °C
    # Optional: Enable overdrive for aggressive heating/cooling
    overdrive_mode: true
    overdrive_heating_temperature: 30  # Used when HVAC mode is 'heat'
    overdrive_cooling_temperature: 16  # Used when HVAC mode is 'cool'
    # Optional: Prevent cooling if temperatures are below thresholds
    min_outside_temperature_for_cooling: 22  # Default: 22°C
    min_inside_temperature_for_cooling: 21   # Default: 21°C
```

See module docstring and inline examples for usage.
"""

import inspect
from datetime import datetime

from base import BaseApp


class ClimateControl(BaseApp):

    def initialize(self):
        super().initialize()
        self.log("Hello from ClimateControl")

        # setup sane defaults
        self._climate_controls = self.args.get("climate_controls", [])

        self._internal_change_timeout = int(self.args.get("internal_change_timeout", 60))

        self._external_temperature_sensor = self.args.get("external_temperature_sensor", None)
        self._outside_temperature_sensor = self.args.get("outside_temperature_sensor", None)
        self._max_overheat_allowance = self.args.get("max_overheat_allowance", 0.5)
        self._fan_overheat_temperature = float(self.args.get("fan_overheat_temperature", 22))
        self._summer_temperature_threshold = float(self.args.get("summer_temperature_threshold", 15))
        self._summer_temperature_threshold_tomorrow = float(self.args.get("summer_temperature_threshold_tomorrow", self._summer_temperature_threshold + 3))
        self._min_outside_temperature_for_cooling = float(self.args.get("min_outside_temperature_for_cooling", 23.0))
        self._min_inside_temperature_for_cooling = float(self.args.get("min_inside_temperature_for_cooling", 20))

        # Temperature bounds - separate for heating and cooling
        self._min_temperature_heating = float(self.args.get("min_temperature_heating", 7))
        self._max_temperature_heating = float(self.args.get("max_temperature_heating", 30))
        self._min_temperature_cooling = float(self.args.get("min_temperature_cooling", 16))
        self._max_temperature_cooling = float(self.args.get("max_temperature_cooling", 30))
        
        self._cooling_temperature = float(self.args.get("cooling_temperature", 22))
        self._cooling_temperature_control = self.args.get("cooling_temperature_control", None)

        self._aqi_sensor = self.args.get("aqi_sensor", None)
        self._aqi_threshold = int(self.args.get("aqi_threshold", 50))

        self._voc_sensor = self.args.get("voc_sensor", None)
        self._voc_threshold = int(self.args.get("voc_threshold", 220))

        self._co2_sensor = self.args.get("co2_sensor", None)
        self._co2_threshold = int(self.args.get("co2_threshold", 800))

        self._humidity_sensor = self.args.get("humidity_sensor", None)

        self._cleanup_air_at_night = self.args.get("cleanup_air_at_night", True)

        # Temperature offsets for calibration - separate for heating and cooling
        self._offset_temperature_heating = float(self.args.get("offset_temperature_heating", 0))
        self._offset_temperature_cooling = float(self.args.get("offset_temperature_cooling", 0))
        
        # PID controller configuration
        self._enable_pid = bool(self.args.get("enable_pid", False))
        self._pid_kp = float(self.args.get("pid_kp", 1.0))
        self._pid_ki = float(self.args.get("pid_ki", 0.1))
        self._pid_kd = float(self.args.get("pid_kd", 0.05))
        self._pid_output_limit = float(self.args.get("pid_output_limit", 6.0))
        
        # PID state tracking per climate control
        self._pid_state = {}
        for climate_control in self._climate_controls:
            self._pid_state[climate_control] = {
                'integral': 0.0,
                'last_error': 0.0,
                'last_time': None,
                'last_status': None,
                'last_hvac_mode': None
            }
        
        # Heating temperatures, controls, and HVAC modes for each status
        self._motion_temperature = float(self.args.get("motion_temperature", 21))
        self._motion_temperature_control = self.args.get("motion_temperature_control", None)
        self._motion_hvac_mode = self.args.get("motion_hvac_mode", "heat")
        self._motion_duration = self.args.get("motion_duration", 300)
        self._home_temperature = float(self.args.get("home_temperature", 20))
        self._home_temperature_control = self.args.get("home_temperature_control", None)
        self._home_hvac_mode = self.args.get("home_hvac_mode", "heat")
        self._night_temperature = float(self.args.get("night_temperature", 18))
        self._night_temperature_control = self.args.get("night_temperature_control", None)
        self._night_hvac_mode = self.args.get("night_hvac_mode", "heat")
        self._away_temperature = float(self.args.get("away_temperature", 18))
        self._away_temperature_control = self.args.get("away_temperature_control", None)
        self._away_hvac_mode = self.args.get("away_hvac_mode", "heat")
        self._vacation_temperature = float(self.args.get("vacation_temperature", 16))
        self._vacation_hvac_mode = self.args.get("vacation_hvac_mode", "heat")
        self._vacation_temperature_control = self.args.get("vacation_temperature_control", None)
        self._open_temperature = float(self.args.get("open_temperature", 16))
        self._open_hvac_mode = self.args.get("open_hvac_mode", "off")
        self._open_temperature_control = self.args.get("open_temperature_control", None)
        
        # Cooling HVAC modes for each status (defaults to 'cool')
        self._motion_hvac_mode_cooling = self.args.get("motion_hvac_mode_cooling", "cool")
        self._home_hvac_mode_cooling = self.args.get("home_hvac_mode_cooling", "cool")
        self._night_hvac_mode_cooling = self.args.get("night_hvac_mode_cooling", "cool")
        self._away_hvac_mode_cooling = self.args.get("away_hvac_mode_cooling", "cool")
        self._vacation_hvac_mode_cooling = self.args.get("vacation_hvac_mode_cooling", "off")
        self._open_hvac_mode_cooling = self.args.get("open_hvac_mode_cooling", "off")
        
        # Cooling temperatures and controls for each status (defaults to cooling_temperature if not set)
        self._motion_temperature_cooling = float(self.args.get("motion_temperature_cooling", self._cooling_temperature))
        self._motion_temperature_control_cooling = self.args.get("motion_temperature_control_cooling", None)
        self._home_temperature_cooling = float(self.args.get("home_temperature_cooling", self._cooling_temperature))
        self._home_temperature_control_cooling = self.args.get("home_temperature_control_cooling", None)
        self._night_temperature_cooling = float(self.args.get("night_temperature_cooling", self._cooling_temperature))
        self._night_temperature_control_cooling = self.args.get("night_temperature_control_cooling", None)
        self._away_temperature_cooling = float(self.args.get("away_temperature_cooling", self._cooling_temperature))
        self._away_temperature_control_cooling = self.args.get("away_temperature_control_cooling", None)
        self._vacation_temperature_cooling = float(self.args.get("vacation_temperature_cooling", self._cooling_temperature))
        self._vacation_temperature_control_cooling = self.args.get("vacation_temperature_control_cooling", None)
        self._open_temperature_cooling = float(self.args.get("open_temperature_cooling", self._cooling_temperature))
        self._open_temperature_control_cooling = self.args.get("open_temperature_control_cooling", None)

        self._overdrive_heating_temperature = float(self.args.get("overdrive_heating_temperature", 30))
        self._overdrive_cooling_temperature = float(self.args.get("overdrive_cooling_temperature", 16))
        self._overdrive_mode = bool(self.args.get("overdrive_mode", False))

        self.log("=== Climate Control Configuration ===")
        self.log(f"Climate controls: {self._climate_controls}")
        self.log(f"External temperature sensor: {self._external_temperature_sensor}")
        self.log(f"Outside temperature sensor: {self._outside_temperature_sensor}")
        self.log(f"Offset temperature heating: {self._offset_temperature_heating}°C")
        self.log(f"Offset temperature cooling: {self._offset_temperature_cooling}°C")
        self.log(f"PID controller: {'Enabled' if self._enable_pid else 'Disabled'}")
        if self._enable_pid:
            self.log(f"PID parameters: Kp={self._pid_kp}, Ki={self._pid_ki}, Kd={self._pid_kd}, Limit=±{self._pid_output_limit}°C")
        self.log(f"Max overheat allowance: {self._max_overheat_allowance}")
        self.log(f"Fan overheat temperature: {self._fan_overheat_temperature}°C")
        self.log(f"Temperature bounds heating: {self._min_temperature_heating}°C - {self._max_temperature_heating}°C")
        self.log(f"Temperature bounds cooling: {self._min_temperature_cooling}°C - {self._max_temperature_cooling}°C")
        self.log(f"Cooling temperature: {self._cooling_temperature}°C, Control: {self._cooling_temperature_control}")
        self.log(f"Internal change timeout: {self._internal_change_timeout}s")
        self.log(f"External change timeout: {self._external_change_timeout}s")
        self.log(f"Overdrive mode: {self._overdrive_mode}, heating target: {self._overdrive_heating_temperature}°C, cooling target: {self._overdrive_cooling_temperature}°C")

        self.log("--- Air Quality Sensors ---")
        self.log(f"AQI sensor: {self._aqi_sensor}, threshold: {self._aqi_threshold}")
        self.log(f"VOC sensor: {self._voc_sensor}, threshold: {self._voc_threshold}")
        self.log(f"CO₂ sensor: {self._co2_sensor}, threshold: {self._co2_threshold}")

        self.log("--- Seasonal Settings ---")
        self.log(f"Summer temperature threshold (today): {self._summer_temperature_threshold}°C")
        self.log(f"Summer temperature threshold (tomorrow): {self._summer_temperature_threshold_tomorrow}°C")
        self.log(f"Min outside temperature for cooling: {self._min_outside_temperature_for_cooling}°C")
        self.log(f"Min inside temperature for cooling: {self._min_inside_temperature_for_cooling}°C")
        self.log("Summer detection: Used for cooling activation logic only, not a status")

        self.log("--- Temperature Modes ---")
        self.log(f"Home: Heat={self._home_temperature}°C/{self._home_hvac_mode} Cool={self._home_temperature_cooling}°C/{self._home_hvac_mode_cooling}, Control: {self._home_temperature_control}/{self._home_temperature_control_cooling}")
        self.log(f"Night: Heat={self._night_temperature}°C/{self._night_hvac_mode} Cool={self._night_temperature_cooling}°C/{self._night_hvac_mode_cooling}, Control: {self._night_temperature_control}/{self._night_temperature_control_cooling}")
        self.log(f"Away: Heat={self._away_temperature}°C/{self._away_hvac_mode} Cool={self._away_temperature_cooling}°C/{self._away_hvac_mode_cooling}, Control: {self._away_temperature_control}/{self._away_temperature_control_cooling}")
        self.log(f"Vacation: Heat={self._vacation_temperature}°C/{self._vacation_hvac_mode} Cool={self._vacation_temperature_cooling}°C/{self._vacation_hvac_mode_cooling}, Control: {self._vacation_temperature_control}/{self._vacation_temperature_control_cooling}")
        self.log(f"Open-window: Heat={self._open_temperature}°C/{self._open_hvac_mode} Cool={self._open_temperature_cooling}°C/{self._open_hvac_mode_cooling}, Control: {self._open_temperature_control}/{self._open_temperature_control_cooling}")
        self.log(f"Motion: Heat={self._motion_temperature}°C/{self._motion_hvac_mode} Cool={self._motion_temperature_cooling}°C/{self._motion_hvac_mode_cooling}, Duration: {self._motion_duration}s, Control: {self._motion_temperature_control}/{self._motion_temperature_control_cooling}")

        self.log("--- Status Overview ---")
        self.log(f"Current system status: {self.get_current_status()}")

        self.log("=== End of Climate Control Configuration ===")

        # stop heating if doors or windows are open
        for sensor in self._opening_sensors:
            self.listen_state(self.sensor_change_callback, sensor,
                                new="on", old="off", duration=self._opening_timeout)
            self.listen_state(self.sensor_change_callback, sensor, 
                                new="off", old="on", duration=self._opening_timeout)
            
        # stop heating if nobody is home
        for sensor in self._device_trackers:
            self.listen_state(self.sensor_change_callback, sensor,
                                new="not_home", old="home", duration=self._tracker_timeout)
            self.listen_state(self.sensor_change_callback,
                                sensor, new="home", old="not_home")

        # stop heating during vacation
        if self._vacation_control is not None:
            self.listen_state(self.sensor_change_callback, 
                               self._vacation_control, new="on", old="off")
            self.listen_state(self.sensor_change_callback,
                                self._vacation_control, new="off", old="on")

        # start heating for guests
        if self._guest_control is not None:
            self.listen_state(self.sensor_change_callback,
                                self._guest_control, new="on", old="off")
            self.listen_state(self.sensor_change_callback,
                                self._guest_control, new="off", old="on")

        # start heating for motion events
        for sensor in self._motion_sensors:
            self.listen_state(self.sensor_change_callback, sensor,
                                new="off", old="on", duration=self._motion_timeout)
            self.listen_state(self.sensor_change_callback, sensor,
                                new="on", old="off")

        # change based on settings in gui - heating controls
        for temptype in ['home', 'away', 'vacation', 'open', 'motion', 'night']:
            if vars(self)['_' + temptype + '_temperature_control'] is not None:
                self.log(f"Listening for {vars(self)['_' + temptype + '_temperature_control']}")
                self.listen_state(self.sensor_change_callback, vars(self)['_' + temptype + '_temperature_control'] )
        
        # change based on settings in gui - cooling controls
        for temptype in ['home', 'away', 'vacation', 'open', 'motion', 'night']:
            if vars(self)['_' + temptype + '_temperature_control_cooling'] is not None:
                self.log(f"Listening for {vars(self)['_' + temptype + '_temperature_control_cooling']}")
                self.listen_state(self.sensor_change_callback, vars(self)['_' + temptype + '_temperature_control_cooling'] )
        
        # listen for default cooling temperature control changes
        if self._cooling_temperature_control is not None:
            self.log(f"Listening for {self._cooling_temperature_control}")
            self.listen_state(self.sensor_change_callback, self._cooling_temperature_control)

        # change based on climate control
        for climate_control in self._climate_controls:
            # record changes
            self.listen_state(self.control_change_callback, climate_control)
            self.listen_state(self.control_change_callback, climate_control, attribute="temperature")
            self.listen_state(self.control_change_callback, climate_control, attribute="fan_mode")
            self.listen_state(self.control_change_callback, climate_control, attribute="preset_mode")
            self.listen_state(self.control_change_callback, climate_control, attribute="swing_mode")
            self.listen_state(self.control_change_callback, climate_control, attribute="swing_horizontal_mode")
            # act on changes delayed
            #self.listen_state(self.sensor_change_callback, climate_control, duration=60)
            #self.listen_state(self.sensor_change_callback, climate_control, attribute="temperature", duration=60)
            #self.listen_state(self.sensor_change_callback, climate_control, attribute="hvac_mode", duration=60)
            #self.listen_state(self.sensor_change_callback, climate_control, attribute="fan_mode", duration=60)
            #self.listen_state(self.sensor_change_callback, climate_control, attribute="preset_mode", duration=60)
            if not self._external_temperature_sensor:
                self.listen_state(self.sensor_change_callback, climate_control, attribute="current_temperature")


        # listen for time changes
        if(self._night_start is not None):
            runtime = self.parse_time(self._night_start)
            self.run_daily(self.periodic_time_callback, runtime)
        if(self._night_end is not None):
            runtime = self.parse_time(self._night_end)
            self.run_daily(self.periodic_time_callback, runtime)
        if(self._night_start_workday is not None and self._night_start != self._night_start_workday):
            runtime = self.parse_time(self._night_start_workday)
            self.run_daily(self.periodic_time_callback, runtime)
        if(self._night_end_workday is not None and self._night_end != self._night_end_workday):
            runtime = self.parse_time(self._night_end_workday)
            self.run_daily(self.periodic_time_callback, runtime)

        if self._external_temperature_sensor:
            self.listen_state(self.sensor_change_callback, self._external_temperature_sensor)

        self.listen_state(self.sensor_change_callback, 'sensor.temperature_max_today')
        self.listen_state(self.sensor_change_callback, 'sensor.temperature_max_tomorrow')
        self.listen_state(self.sensor_change_callback, 'weather.forecast_home')

        # Set start time to now, aligning to the next full 10-minute mark
        self.run_every(self.periodic_time_callback, "now+10", 10 * 60)

    def is_overheating(self):
        """Return True if external temperature indicates overheating.

        Uses configured max overheat allowance to determine if the external
        temperature significantly exceeds the desired temperature.

        Returns:
            bool
        """
        if self.get_external_temperature() is None:
            return False

        return self.get_external_temperature() > self.get_desired_temperature() + self._max_overheat_allowance

    def is_cooling(self, entity_id):
        """Return True if the given entity is currently in cooling mode.

        Args:
            entity_id (str): climate entity id to query.

        Returns:
            bool
        """
        return self.get_current_hvac_mode(entity_id) == 'cool'

    def is_summer(self):
        """Return True when outside/forecast temperatures indicate 'summer' mode.

        Compares current/forecasted temperatures to configured summer thresholds.
        """
        return (self.get_outside_temperature() > self._summer_temperature_threshold or
                self.get_max_outside_temperature_today() > self._summer_temperature_threshold or
                self.get_max_outside_temperature_tomorrow() > self._summer_temperature_threshold_tomorrow)

    def is_aqi_okay(self):
        """Return True if AQI measurement is below configured threshold.

        Returns True if no AQI sensor is configured or the reading is unavailable.
        """
        value_sensor = self.get_aqi_measurement()
        if value_sensor is None:
            return True

        return not int(value_sensor) > self._aqi_threshold

    def is_voc_okay(self):
        """Return True if VOC measurement is below configured threshold.

        Returns True if no VOC sensor is configured or the reading is unavailable.
        """
        value_sensor = self.get_voc_measurement()
        if value_sensor is None:
            return True

        return not int(value_sensor) > self._voc_threshold

    def is_co2_okay(self):
        """Return True if CO2 measurement is below configured threshold.

        Returns True if no CO2 sensor is configured or the reading is unavailable.
        """
        value_sensor = self.get_co2_measurement()
        if value_sensor is None:
            return True

        return not int(value_sensor) > self._co2_threshold

    def in_guest_mode(self):
        """Return True when guest mode is enabled (via configured guest_control)."""
        if self._guest_control is None:
            return False
        return self.get_state(self._guest_control) == 'on'

    def in_vacation_mode(self):
        """Return True when vacation mode is active (via configured vacation_control)."""
        if self._vacation_control is None:
            return False
        return self.get_state(self._vacation_control) == 'on'

    def get_current_status(self):
        """Determine the current climate status string.

        Possible return values: 'open', 'vacation', 'night', 'home', 'away', 'motion'.
        """
        if(self.count_on_opening_sensors() > 0):
            return "open"
        elif(self.in_vacation_mode()):
            return "vacation"
        elif(self.is_time_in_night_window()):
            return "night"
        elif(self.in_guest_mode()):
            return "home"
        elif(self.count_home_device_trackers() == 0):
            return "away"
        elif(self.count_on_motion_sensors() > 0):
            return "motion"
        return "home"

    def get_aqi_measurement(self):
        """Return integer AQI measurement or None when unavailable."""
        if self._aqi_sensor is None:
            return None

        value_sensor = self.get_state(self._aqi_sensor)
        if value_sensor == 'unknown':
            return None
        if value_sensor == 'unavailable':
            return None
        if value_sensor is None:
            return None

        return int(value_sensor)

    def get_voc_measurement(self):
        """Return integer VOC measurement or None when unavailable."""
        if self._voc_sensor is None:
            return None

        value_sensor = self.get_state(self._voc_sensor)
        if value_sensor == 'unknown':
            return None
        if value_sensor == 'unavailable':
            return None
        if value_sensor is None:
            return None

        return int(value_sensor)

    def get_co2_measurement(self):
        """Return integer CO2 measurement or None when unavailable."""
        if self._co2_sensor is None:
            return None

        value_sensor = self.get_state(self._co2_sensor)
        if value_sensor == 'unknown':
            return None
        if value_sensor == 'unavailable':
            return None
        if value_sensor is None:
            return None

        return int(value_sensor)

    def get_humidity_measurement(self):
        """Return humidity as float or None when unavailable."""
        if self._humidity_sensor is None:
            return None

        value_sensor = self.get_state(self._humidity_sensor)
        if value_sensor == 'unknown':
            return None
        if value_sensor == 'unavailable':
            return None
        if value_sensor is None:
            return None

        return float(value_sensor)

    def get_external_temperature(self):
        """Return external temperature as float or None when unavailable."""
        if self._external_temperature_sensor is None:
            return None

        value_sensor = self.get_state(self._external_temperature_sensor)
        if value_sensor == 'unknown':
            return None
        if value_sensor == 'unavailable':
            return None
        if value_sensor is None:
            return None

        return float(value_sensor)

    def get_outside_temperature(self):
        """Return the outside temperature, combining sensor and forecast when both available.

        Returns a float; 0 if no forecast is available.
        """
        value_sensor = None
        value_forecast = self.get_state('weather.forecast_home', attribute = "temperature")
        if value_forecast == 'unknown':
            value_forecast = None
        if value_forecast == 'unavailable':
            value_forecast = None

        if self._outside_temperature_sensor is not None:
            value_sensor = self.get_state(self._outside_temperature_sensor)
            if value_sensor == 'unknown':
                value_sensor = None
            if value_sensor == 'unavailable':
                value_sensor = None

        if value_sensor is not None and value_forecast is not None:
            return max(float(value_sensor), float(value_forecast))

        if value_forecast is None:
            return 0

        return float(value_forecast)

    def get_max_outside_temperature_today(self):
        """Return today's maximum outside temperature as float (or 0 if unknown)."""
        value = self.get_state('sensor.temperature_max_today')
        if value is None:
            return 0
        if value == 'unknown':
            return 0
        if value == 'unavailable':
            return 0
        return float(value)

    def get_max_outside_temperature_tomorrow(self):
        """Return tomorrow's maximum outside temperature as float (or 0 if unknown)."""
        value = self.get_state('sensor.temperature_max_tomorrow')
        if value is None:
            return 0
        if value == 'unknown':
            return 0
        if value == 'unavailable':
            return 0
        return float(value)

    def get_desired_temperature_by_status(self, status):
        """Return desired temperature for the given status.

        Automatically determines whether to use heating or cooling temperature
        based on summer detection (is_summer()).
        
        The value is read from a temperature control entity when configured,
        otherwise from the configured default temperature for the status.
        Does NOT apply offset - that's done in get_desired_target_temperature().

        Args:
            status (str): status name such as 'home', 'night', 'away', etc.

        Returns:
            float or None: desired temperature (without offset) or None if not set.
        """
        # Determine which attribute suffix to use based on summer detection
        suffix = '_cooling' if self.is_summer() else ''
        
        # Check for control entity first
        control_attr = '_' + status + '_temperature_control' + suffix
        if control_attr in vars(self) and vars(self)[control_attr] is not None:
            return float(self.get_state(vars(self)[control_attr]))
        
        # Fall back to configured temperature
        temp_attr = '_' + status + '_temperature' + suffix
        if temp_attr in vars(self) and vars(self)[temp_attr] is not None:
            return float(vars(self)[temp_attr])
        
        # If cooling temperature not configured, fall back to default cooling_temperature
        # This maintains backward compatibility
        if self.is_summer() and suffix == '_cooling':
            self.log(f"No cooling temperature configured for {status}, using default cooling_temperature", level="DEBUG")
            return self._cooling_temperature
        
        self.log(f"No temperature configured for status={status}", level="DEBUG")
        return None

    def get_desired_temperature(self):
        """Return the effective desired temperature considering status, minimum, and maximum.

        Automatically determines whether to use heating or cooling bounds
        based on summer detection (is_summer()).

        Returns the desired temperature for the current status, bounded by the
        configured minimum and maximum temperature.
        """
        desired_temp = self.get_desired_temperature_by_status(self.get_current_status())
        if desired_temp is None:
            return self._min_temperature_cooling if self.is_summer() else self._min_temperature_heating
        
        if self.is_summer():
            return float(min(max(desired_temp, self._min_temperature_cooling), self._max_temperature_cooling))
        else:
            return float(min(max(desired_temp, self._min_temperature_heating), self._max_temperature_heating))

    def calculate_pid_offset(self, entity_id, current_temp, desired_temp, hvac_mode):
        """Calculate PID controller offset for dynamic temperature adjustment.
        
        Args:
            entity_id (str): climate entity id
            current_temp (float): current measured temperature
            desired_temp (float): desired target temperature (without PID)
            hvac_mode (str): current HVAC mode
            
        Returns:
            float: PID offset to add to the target temperature
        """
        if not self._enable_pid or entity_id not in self._pid_state:
            return 0.0
            
        # Reset and return 0 if HVAC mode is off or fan_only (no active heating/cooling)
        if hvac_mode in ['off', 'fan_only']:
            pid_state = self._pid_state[entity_id]
            if pid_state['integral'] != 0.0 or pid_state['last_error'] != 0.0:
                self.log(f"[{entity_id}] PID: Resetting state due to inactive HVAC mode ({hvac_mode})", level="DEBUG")
                pid_state['integral'] = 0.0
                pid_state['last_error'] = 0.0
                pid_state['last_time'] = None
                pid_state['last_status'] = None
                pid_state['last_hvac_mode'] = None
            return 0.0
            
        current_status = self.get_current_status()
        pid_state = self._pid_state[entity_id]
        current_time = datetime.now().astimezone()
        
        # Reset PID state if status or HVAC mode changed
        if (pid_state['last_status'] != current_status or 
            pid_state['last_hvac_mode'] != hvac_mode):
            self.log(f"[{entity_id}] PID: Resetting state due to status/mode change", level="DEBUG")
            pid_state['integral'] = 0.0
            pid_state['last_error'] = 0.0
            pid_state['last_time'] = current_time
            pid_state['last_status'] = current_status
            pid_state['last_hvac_mode'] = hvac_mode
            return 0.0
            
        # Calculate error (negative = too cold, positive = too hot)
        error = current_temp - desired_temp
        
        # Initialize on first run
        if pid_state['last_time'] is None:
            pid_state['last_time'] = current_time
            pid_state['last_error'] = error
            return 0.0
            
        # Calculate time delta
        dt = (current_time - pid_state['last_time']).total_seconds()
        if dt <= 0:
            return 0.0
            
        # PID calculations
        # Proportional term
        p_term = self._pid_kp * error
        
        # Integral term (accumulated error over time)
        pid_state['integral'] += error * dt
        # Anti-windup: limit integral to prevent excessive accumulation
        max_integral = self._pid_output_limit / max(self._pid_ki, 0.001)
        pid_state['integral'] = max(min(pid_state['integral'], max_integral), -max_integral)
        i_term = self._pid_ki * pid_state['integral']
        
        # Derivative term (rate of change)
        derivative = (error - pid_state['last_error']) / dt
        d_term = self._pid_kd * derivative
        
        # Calculate total PID output
        pid_output = p_term + i_term + d_term
        
        # Apply output limits
        pid_output = max(min(pid_output, self._pid_output_limit), -self._pid_output_limit)
        
        # Update state
        pid_state['last_error'] = error
        pid_state['last_time'] = current_time
        
        self.log(f"[{entity_id}] PID: error={error:.2f}°C, P={p_term:.2f}, I={i_term:.2f}, D={d_term:.2f}, output={pid_output:.2f}°C", level="DEBUG")
        
        return pid_output

    def get_desired_target_temperature(self, entity_id = None):
        """Return the desired target temperature with mode-specific offset, PID control, and overdrive logic.

        Applies the appropriate static offset and min/max bounds based on season (is_summer()),
        then adds dynamic PID offset if enabled, and finally applies overdrive if configured.
        
        Args:
            entity_id (str|None): optional climate entity id to determine the actual desired mode
        """
        # Use the computed desired HVAC mode (which considers overheating, air quality, etc.)
        # not just the status-based mode
        hvac_mode = self.get_desired_hvac_mode(entity_id)
        
        # Get base temperature with static offset and bounds applied
        # Use is_summer() to determine which offset/bounds to apply (not hvac_mode)
        # This ensures correct offset even when HVAC is 'off' or 'fan_only'
        if self.is_summer():
            # Cooling season: use cooling temps, offset, and bounds
            raw_temp = self.get_desired_temperature_by_status(self.get_current_status())
            if raw_temp is None:
                raw_temp = self._min_temperature_cooling
            base_temp = raw_temp + self._offset_temperature_cooling
            # Apply cooling-specific min/max bounds
            desired_temp = float(min(max(base_temp, self._min_temperature_cooling), self._max_temperature_cooling))
        else:
            # Heating season: use heating temps, offset, and bounds
            raw_temp = self.get_desired_temperature_by_status(self.get_current_status())
            if raw_temp is None:
                raw_temp = self._min_temperature_heating
            base_temp = raw_temp + self._offset_temperature_heating
            # Apply heating-specific min/max bounds
            desired_temp = float(min(max(base_temp, self._min_temperature_heating), self._max_temperature_heating))

        # Apply PID controller adjustment if enabled and external temperature is available
        if self._enable_pid and entity_id is not None and self.get_external_temperature() is not None:
            current_temp = self.get_external_temperature()
            # Calculate PID offset based on error (for heating: positive offset when too cold)
            pid_offset = self.calculate_pid_offset(entity_id, current_temp, desired_temp, hvac_mode)
            
            # Apply PID offset for heating (positive offset when too cold, negative offset when too hot)
            desired_temp_with_pid = desired_temp - pid_offset

            if hvac_mode == 'cool':
                # Re-apply bounds after PID adjustment (based on hvac_mode)
                desired_temp = float(min(max(desired_temp_with_pid, self._min_temperature_cooling), self._max_temperature_cooling))
            elif hvac_mode == 'heat':
                # Re-apply bounds after PID adjustment (based on hvac_mode)
                desired_temp = float(min(max(desired_temp_with_pid, self._min_temperature_heating), self._max_temperature_heating))

        # Apply overdrive if enabled (overrides everything)
        if self._overdrive_mode and self.get_external_temperature() is not None:
            if hvac_mode == 'heat':
                desired_temp = self._overdrive_heating_temperature
                self.log(f"Overdrive heating active: targeting {desired_temp}°C", level="DEBUG")
            elif hvac_mode == 'cool':
                desired_temp = self._overdrive_cooling_temperature
                self.log(f"Overdrive cooling active: targeting {desired_temp}°C", level="DEBUG")

        return desired_temp
    
    def get_temperature_difference(self, entity_id):
        """Return the difference between current and desired temperature.

        Returns:
            float: current temperature - desired temperature.
        """

        if self.get_external_temperature() is None:
            current_temp = self.get_current_temperature(entity_id)
        else:
            current_temp = self.get_external_temperature()
        desired_temp = self.get_desired_temperature()

        return current_temp - desired_temp

    def get_desired_hvac_mode_by_status(self, status):
        """Return the desired HVAC mode configured for a given status.
        
        Automatically determines whether to use heating or cooling HVAC mode
        based on summer detection (is_summer()).
        
        Args:
            status (str): status name such as 'home', 'night', 'away', etc.
            
        Returns:
            str: desired HVAC mode string (e.g., 'heat', 'cool', 'off', 'fan_only').
        """
        # Determine which attribute suffix to use based on summer detection
        suffix = '_cooling' if self.is_summer() else ''
        attr_name = '_' + status + '_hvac_mode' + suffix
        
        # Return the configured HVAC mode, falling back to heating mode if cooling not configured
        if attr_name in vars(self):
            return vars(self)[attr_name]
        
        # Fallback to heating mode for backward compatibility
        return vars(self)['_' + status + '_hvac_mode']

    def get_desired_hvac_mode(self, entity_id = None):
        """Compute desired HVAC mode for the current status and entity.

        The computed mode considers overheating, air quality and device fan support.
        Automatically determines whether to use heating or cooling mode based on conditions.

        Args:
            entity_id (str|None): optional climate entity id used to check feature support.

        Returns:
            str: desired HVAC mode string.
        """
        # Get base desired mode (automatically uses summer detection internally)
        desired_mode = self.get_desired_hvac_mode_by_status(self.get_current_status())

        fan_supported = False
        if entity_id is not None:
            fan_supported = self.is_fan_mode_supported(entity_id, 'Auto')

        cooling_supported = False
        if entity_id is not None:
            cooling_supported = self.is_hvac_mode_supported(entity_id, 'cool')


        if self.is_summer():
            # In summer, base mode might be 'cool', but we should only cool when actually needed
            # If it's summer but not currently warm enough for cooling, default to 'off' instead
            if (cooling_supported
                and desired_mode == 'cool'
                and self.get_external_temperature() is not None
                and (
                    self.get_external_temperature() < self._min_inside_temperature_for_cooling
                    or self.get_outside_temperature() < self._min_outside_temperature_for_cooling
                    or self.get_max_outside_temperature_today() < self._min_outside_temperature_for_cooling)
                ):
                desired_mode = 'off'
                self.log(f"Summer mode but too cold for cooling (inside: {self.get_external_temperature()}°C, outside: {self.get_outside_temperature()}°C), setting to off", level="DEBUG")
            if (not cooling_supported):
                desired_mode = 'off'
                self.log("Summer mode but cooling not supported by device, setting to off", level="DEBUG")

        else:
            # In winter, if overheating is detected, we may want to turn off heating or use fan_only
            if self.is_overheating():
                # winter fan support to distribute heat when somebody is home and it is daytime
                if (
                    fan_supported
                    and self.is_somebody_at_home()
                    and self.get_external_temperature() > self._fan_overheat_temperature
                    and not self.is_time_in_night_window()
                ):
                    desired_mode = 'fan_only'
                else:
                    desired_mode = 'off'

                self.log(f"Setting desired HVAC mode to {desired_mode} to reduce overheat", level="DEBUG")

        if desired_mode == 'off' and fan_supported:
            # If air quality is poor, someone is home, no windows are open and
            # either it's not night or night-time cleanup is allowed, then use
            # fan_only instead of remaining off.
            air_bad = (not self.is_aqi_okay()) or (not self.is_voc_okay())
            someone_home = self.is_somebody_at_home()
            windows_closed = self.count_on_opening_sensors() == 0
            night_ok = (not self.is_time_in_night_window()) or self.is_cleanup_air_at_night_enabled()

            if air_bad and someone_home and windows_closed and night_ok:
                self.log("Setting desired HVAC mode to fan_only due to bad air", level="DEBUG")
                desired_mode = 'fan_only'

        return desired_mode

    def is_cleanup_air_at_night_enabled(self):
        """Return True if air cleanup at night is enabled."""
        return self._cleanup_air_at_night

    def get_current_temperature(self, entity_id):
        """Return the current measured temperature for a climate entity.

        Returns 0 when the reading is missing/unavailable.
        """
        value = self.get_state(entity_id, attribute = "current_temperature")
        if value is None:
            return 0
        if value == 'unknown':
            return 0
        if value == 'unavailable':
            return 0
        return float(value)

    def get_target_temperature(self, entity_id):
        """Return the target temperature configured on the climate entity."""
        value = self.get_state(entity_id, attribute = "temperature")
        if value is None:
            return 0
        if value == 'unknown':
            return 0
        if value == 'unavailable':
            return 0
        return float(value)

    def get_current_fan_mode(self, entity_id):
        """Return the current fan mode attribute of a climate entity."""
        return self.get_state(entity_id, attribute = "fan_mode")

    def get_desired_fan_mode(self, entity_id = None):
        """Compute the desired fan mode based on air quality and time.

        If an entity is provided, the function first checks whether the entity
        supports the configured 'Auto' option. Returns None when unsupported.
        """
        desired_mode = "Auto"

        if entity_id is not None and not self.is_fan_mode_supported(entity_id, 'Auto'):
            return None

        if self.is_time_in_night_window():
            return desired_mode

        mapping = {
            0: 'Auto',
            1: 'Mid',
            2: 'HighMid',
            3: 'High',
        }

        aqi_value = 0
        if self.get_aqi_measurement() is not None:
            aqi_reading = self.get_aqi_measurement()
            if aqi_reading > self._aqi_threshold * 3:
                aqi_value = 3
            elif aqi_reading > self._aqi_threshold * 2:
                aqi_value = 2
            elif aqi_reading > self._aqi_threshold * 1.5:
                aqi_value = 1
            elif aqi_reading > self._aqi_threshold:
                aqi_value = 0

        voc_value = 0
        if self.get_voc_measurement() is not None:
            voc_reading = self.get_voc_measurement()
            if voc_reading > self._voc_threshold * 10:
                voc_value = 3
            elif voc_reading > self._voc_threshold * 3:
                voc_value = 2
            elif voc_reading > self._voc_threshold * 1.5:
                voc_value = 1
            elif voc_reading > self._voc_threshold:
                voc_value = 0

        desired_mode = mapping[max(0, aqi_value, voc_value)]

        return desired_mode

    def set_optimal_fan_mode(self, entity_id):
        """Set the fan mode on the entity to the computed optimal value.

        Performs support checks.
        """
        if self.get_desired_fan_mode() is None:
            self.log(f"[{entity_id}] Cannot set optimal fan mode: Desired setting is None.", level="ERROR")
            return

        if self.get_desired_hvac_mode(entity_id) == 'off':
            self.log(f"[{entity_id}] Cannot set optimal fan mode: Desired HVAC mode is off.")
            return

        if self.get_current_fan_mode(entity_id) == self.get_desired_fan_mode(entity_id):
            self.log(f"[{entity_id}] Optimal fan mode is already set.")
            return

        if not self.is_fan_mode_supported(entity_id, self.get_desired_fan_mode(entity_id)):
            self.log(f"[{entity_id}] Cannot set optimal fan mode: Device does not support fan mode {self.get_desired_fan_mode(entity_id)}.", level="ERROR")
            return

        self.set_fan_mode(entity_id, self.get_desired_fan_mode(entity_id))

    def get_current_hvac_action(self, entity_id):
        """Return the current hvac_action attribute for a climate entity."""
        return self.get_state(entity_id, attribute = "hvac_action")

    def get_current_preset_mode(self, entity_id):
        """Return the current preset_mode attribute for a climate entity."""
        return self.get_state(entity_id, attribute = "preset_mode")

    def get_desired_preset_mode(self, entity_id = None):
        """Return the desired preset mode (defaults to 'quiet').

        Returns None if the entity doesn't support the desired preset.
        Switches to 'powerful' when far from target temperature (>3°C difference).
        At night, always stays 'quiet' to avoid noise.
        """
        desired_mode = "quiet"

        if entity_id is not None and not self.is_preset_mode_supported(entity_id, 'quiet'):
            return None
        
        # At night, always use quiet mode to avoid noise
        if self.is_time_in_night_window():
            return desired_mode
            
        if self.get_external_temperature() is not None:
            hvac_mode = self.get_desired_hvac_mode(entity_id)
            temp_diff = self.get_temperature_difference(entity_id)
            
            # Use powerful mode when far from target:
            # - Heating: when room is too cold (diff < -3)
            # - Cooling: when room is too hot (diff > 3)
            if hvac_mode == 'heat' and temp_diff < -3 or hvac_mode == 'cool' and temp_diff > 3:
                desired_mode = "powerful"

        return desired_mode

    def set_optimal_preset_mode(self, entity_id):
        """Set the optimal preset mode on the entity, with checks for support and state."""
        if self.get_desired_preset_mode() is None:
            self.log(f"[{entity_id}] Cannot set optimal preset mode: Desired setting is None.")
            return

        if self.get_desired_hvac_mode(entity_id) == 'off':
            self.log(f"[{entity_id}] Cannot set optimal preset mode: Desired HVAC mode is off.")
            return

        if self.get_current_preset_mode(entity_id) == self.get_desired_preset_mode(entity_id):
            self.log(f"[{entity_id}] Optimal preset mode is already set.")
            return

        if not self.is_preset_mode_supported(entity_id, self.get_desired_preset_mode(entity_id)):
            self.log(f"[{entity_id}] Cannot set optimal preset mode: Device does not support preset mode {self.get_desired_preset_mode(entity_id)}.", level="ERROR")
            return

        self.set_preset_mode(entity_id, self.get_desired_preset_mode(entity_id))

    def get_current_hvac_mode(self, entity_id):
        """Return the current HVAC mode (state) of the climate entity."""
        return self.get_state(entity_id)

    def set_optimal_hvac_mode(self, entity_id):
        """Apply the desired HVAC mode to the entity if it's supported and needed."""
        if self.get_desired_hvac_mode() is None:
            self.log(f"[{entity_id}] Cannot set optimal HVAC mode: Desired setting is None.", level="ERROR")
            return

        if self.get_current_hvac_mode(entity_id) == self.get_desired_hvac_mode(entity_id):
            self.log(f"[{entity_id}] Optimal HVAC mode is already set.")
            return

        self.set_hvac_mode(entity_id, self.get_desired_hvac_mode(entity_id))

    def set_optimal_temperature(self, entity_id):
        """Enforce the desired temperature on the entity with safety checks.

        Avoids making changes when HVAC is off or in fan_only mode.
        Records the change as an internal change.
        """
        if self.get_desired_temperature() is None:
            self.log(f"[{entity_id}] Cannot set optimal temperature: Desired temperature is None.", level="ERROR")
            return

        if self.get_desired_hvac_mode(entity_id) == 'off':
            self.log(f"[{entity_id}] Cannot set optimal temperature: Desired HVAC mode is off.")
            return

        if self.get_desired_hvac_mode(entity_id) == 'fan_only':
            self.log(f"[{entity_id}] Cannot set optimal temperature: Desired HVAC mode is fan_only (temperature not applicable).")
            return

        # if self.is_overheating():
        #     self.log(f"[{entity_id}] Cannot set optimal temperature: Room is overheating.")
        #     return

        if self.get_target_temperature(entity_id) == self.get_desired_target_temperature(entity_id):
            self.log(f"[{entity_id}] Optimal temperature is already set.")
            return

        self.set_temperature(entity_id, self.get_desired_target_temperature(entity_id))

    def periodic_time_callback(self, kwargs):
        """Scheduled callback executed at configured times to trigger updates."""
        self.log(f"{inspect.currentframe().f_code.co_name}")

        self.update_climate()

    def control_change_callback(self, entity, attribute, old, new, kwargs):
        """Handle state changes originating from climate control entities.

        Ignores external changes that match the desired settings to avoid
        reacting to legitimate manual adjustments.
        """
        self.log(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        if self.is_current_change_external():
            if attribute == 'temperature' and new == self.get_desired_temperature():
                self.log("Ignoring externl change because it matches the desired temperature")
                return
            # if attribute == 'temperature' and new == self._min_temperature_heating and self.get_current_hvac_mode(entity) == 'off':
            #     self.log("Ignoring externl change because it matches expected temperature for HVAC mode off")
            #     return
            if attribute == 'state' and new == self.get_desired_hvac_mode(entity):
                self.log("Ignoring externl change because it matches the desired HVAC mode")
                return
            if attribute == 'fan_mode' and new == self.get_desired_fan_mode(entity):
                self.log("Ignoring externl change because it matches the desired fan mode")
                return
            if attribute == 'preset_mode' and new == self.get_desired_preset_mode(entity):
                self.log("Ignoring externl change because it matches the desired preset mode")
                return

        super().control_change_callback(entity, attribute, old, new, kwargs)

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        """Handle generic sensor changes and trigger an immediate climate update."""
        self.log(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        self.update_climate()

    def update_climate(self):
        """Main update loop: evaluate status and apply optimal settings to devices.

        Logs overview information and enforces temperature, hvac, fan and preset
        modes when internal change policy allows it.
        """
        self.log("=== Updating climate controls ===")
        
        # Status and temperature overview
        summer_status = "ON" if self.is_summer() else "OFF"
        self.log(f"Status: {self.get_current_status()} | Summer: {summer_status} | External: {self.get_external_temperature()}°C | Desired: {self.get_desired_temperature()}°C | Outside: {self.get_outside_temperature()}°C | Max today/tomorrow: {self.get_max_outside_temperature_today()}°C/{self.get_max_outside_temperature_tomorrow()}°C")
        
        # Air quality measurements (only if available)
        air_quality = []
        if self.get_aqi_measurement() is not None:
            air_quality.append(f"AQI: {self.get_aqi_measurement()}")
        if self.get_voc_measurement() is not None:
            air_quality.append(f"VOC: {self.get_voc_measurement()}µg/m³")
        if self.get_co2_measurement() is not None:
            air_quality.append(f"CO₂: {self.get_co2_measurement()}ppm")
        
        if air_quality:
            self.log(f"Air Quality: {' | '.join(air_quality)}")

        # Check for critical conditions (compact warnings)
        warnings = []
        if not self.is_aqi_okay():
            warnings.append(f"AQI: {self.get_aqi_measurement()}")
        if not self.is_voc_okay():
            warnings.append(f"VOC: {self.get_voc_measurement()}µg/m³")
        if not self.is_co2_okay():
            warnings.append(f"CO₂: {self.get_co2_measurement()}ppm")
        if self.is_overheating():
            warnings.append(f"Overheating: {self.get_external_temperature()}°C")
        
        if warnings:
            self.log(f"⚠️  CRITICAL CONDITIONS: {' | '.join(warnings)}", level="WARNING")

        for climate_control in self._climate_controls:

            # Temperature status
            desired_target = self.get_desired_target_temperature(climate_control)
            self.log(f"[{climate_control}] Temp: {self.get_current_temperature(climate_control)}°C (current) | {self.get_target_temperature(climate_control)}°C (target) | {desired_target}°C (desired w/ offsets)")
            
            # Add PID info if enabled
            if self._enable_pid and climate_control in self._pid_state:
                pid_state = self._pid_state[climate_control]
                self.log(f"[{climate_control}] PID: I={pid_state['integral']:.2f} | LastErr={pid_state['last_error']:.2f} | LastTime={pid_state['last_time']} | LastStatus={pid_state['last_status']} | LastHVAC={pid_state['last_hvac_mode']}")

            # HVAC mode status
            self.log(f"[{climate_control}] HVAC Mode: {self.get_current_hvac_mode(climate_control)} (current) → {self.get_desired_hvac_mode(climate_control)} (desired)")

            # Fan and preset modes (only if supported)
            mode_info = []
            mode_info.append(f"HVAC Action: {self.get_current_hvac_action(climate_control)}")
            if self.is_fan_mode_supported(climate_control):
                mode_info.append(f"Fan: {self.get_current_fan_mode(climate_control)} → {self.get_desired_fan_mode(climate_control)}")
            if self.is_preset_mode_supported(climate_control):
                mode_info.append(f"Preset: {self.get_current_preset_mode(climate_control)} → {self.get_desired_preset_mode(climate_control)}")
            
            if mode_info:
                self.log(f"[{climate_control}] {' | '.join(mode_info)}")

            if(self.is_internal_change_allowed()):
                self.set_optimal_hvac_mode(climate_control)
                self.set_optimal_temperature(climate_control)
                if self.is_fan_mode_supported(climate_control):
                    self.set_optimal_fan_mode(climate_control)
                if self.is_preset_mode_supported(climate_control):
                    self.set_optimal_preset_mode(climate_control)
            else:
                remaining_seconds = self.get_remaining_seconds_before_internal_change_is_allowed()
                self.log(f"[{climate_control}] Doing nothing: Internal change is not allowed for {remaining_seconds:.0f}s.")


    def set_temperature(self, entity_id, temperature):
        """Set the temperature on the entity via Home Assistant service.

        Performs basic validation and records the change as internal.
        """
        self.log(f"[{entity_id}] Changing temperature from {self.get_target_temperature(entity_id)} to {temperature}")

        if temperature is None:
            self.error(f"[{entity_id}] Cannot set temperature to None", level="ERROR")
            return

        if self.get_target_temperature(entity_id) == temperature:
            self.log(f"[{entity_id}] Is already at temperature {temperature}")
            return

        self.log(f"Calling service climate/set_temperature with entity_id {entity_id} and temperature: {temperature}")

        self.call_service("climate/set_temperature",
                            entity_id=entity_id, temperature=temperature)

        self.record_internal_change()

    def is_hvac_mode_supported(self, entity_id, hvac_mode):
        """Return True if the climate entity supports the given HVAC mode.

        Handles hvac_modes being provided as a comma-separated string or a list.
        """
        hvac_modes = self.get_state(entity_id, attribute='hvac_modes')
        if hvac_modes is None:
            return False
        # If it's a string, split it
        if isinstance(hvac_modes, str):
            valid_modes = [mode.strip() for mode in hvac_modes.split(',')]
        elif isinstance(hvac_modes, list):
            valid_modes = [str(mode).strip() for mode in hvac_modes]
        else:
            return False
        return hvac_mode in valid_modes

    def set_hvac_mode(self, entity_id, hvac_mode):
        """Set the hvac_mode on the climate entity after validation.

        Args:
            entity_id (str): climate entity id.
            hvac_mode (str): desired HVAC mode.
        """
        self.log(f"[{entity_id}] Changing hvac_mode from {self.get_current_hvac_mode(entity_id)} to {hvac_mode}")

        if hvac_mode is None:
            self.error(f"[{entity_id}] Cannot set hvac_mode to None", level="ERROR")
            return

        if not self.is_hvac_mode_supported(entity_id, hvac_mode):
            self.log(f"[{entity_id}] Does not support hvac_mode {hvac_mode}", level="ERROR")
            return

        if self.get_current_hvac_mode(entity_id) == hvac_mode:
            self.log(f"[{entity_id}] Is already in hvac_mode {hvac_mode}")
            return

        self.log(f"Calling service climate/set_hvac_mode with entity_id {entity_id} and hvac_mode: {hvac_mode}")

        self.call_service("climate/set_hvac_mode",
                        entity_id=entity_id, hvac_mode=hvac_mode)

        self.record_internal_change()

    def is_fan_mode_supported(self, entity_id, fan_mode = None):
        """Return True if the fan mode is supported by the entity.

        If fan_mode is None, returns True when the entity reports any fan_modes.
        """
        fan_modes = self.get_state(entity_id, attribute='fan_modes')
        self.log(f"[{entity_id}] Got fan modes: {fan_modes}", level="DEBUG")
        if fan_modes is None:
            return False
        if fan_mode is None:
            return True
        self.log(f"[{entity_id}] Fan mode {fan_mode} in valid fan modes {fan_modes}: {fan_mode in fan_modes}", level="DEBUG")
        return fan_mode in fan_modes

    def set_fan_mode(self, entity_id, fan_mode = 'Auto'):
        """Set the fan mode on the entity after validation and record it."""
        self.log(f"[{entity_id}] Changing fan_mode from {self.get_current_fan_mode(entity_id)} to {fan_mode}")

        if fan_mode is None:
            self.error(f"[{entity_id}] Cannot set fan_mode to None", level="ERROR")
            return

        if not self.is_fan_mode_supported(entity_id, fan_mode):
            self.log(f"[{entity_id}] Does not support fan_mode {fan_mode}", level="ERROR")
            return

        if self.get_current_fan_mode(entity_id) == fan_mode:
            self.log(f"[{entity_id}] Is already in fan_mode {fan_mode}")
            return

        self.log(f"Calling service climate/set_fan_mode with entity_id {entity_id} and fan_mode: {fan_mode}")

        self.call_service("climate/set_fan_mode",
                        entity_id=entity_id, fan_mode=fan_mode)

        self.record_internal_change()
        #Auto, Low, LowMid, Mid, HighMid, High

    def is_preset_mode_supported(self, entity_id, preset_mode = None):
        """Return True if the entity supports the given preset mode.

        If preset_mode is None, returns True when any presets are reported.
        """
        preset_modes = self.get_state(entity_id, attribute='preset_modes')
        self.log(f"[{entity_id}] Got preset modes: {preset_modes}", level="DEBUG")
        if preset_modes is None:
            return False
        if preset_mode is None:
            return True
        self.log(f"[{entity_id}] preset mode {preset_mode} in valid preset modes {preset_modes}: {preset_mode in preset_modes}", level="DEBUG")
        return preset_mode in preset_modes

    def set_preset_mode(self, entity_id, preset_mode = 'none'):
        """Set the preset_mode on the climate entity after validation.

        Records the change as internal so future external changes can be ignored
        for a short time.
        """
        self.log(f"[{entity_id}] Changing preset_mode from {self.get_current_preset_mode(entity_id)} to {preset_mode}")

        if preset_mode is None:
            self.error(f"[{entity_id}] Cannot set preset_mode to None", level="ERROR")
            return

        if not self.is_preset_mode_supported(entity_id, preset_mode):
            self.log(f"[{entity_id}] Does not support preset_mode {preset_mode}", level="ERROR")
            return

        if self.get_current_preset_mode(entity_id) == preset_mode:
            self.log(f"[{entity_id}] Is already in preset_mode {preset_mode}")
            return

        self.log(f"Calling service climate/set_preset_mode with entity_id {entity_id} and preset_mode: {preset_mode}")

        self.call_service("climate/set_preset_mode",
                        entity_id=entity_id, preset_mode=preset_mode)

        self.record_internal_change()
        #none, quiet, powerful