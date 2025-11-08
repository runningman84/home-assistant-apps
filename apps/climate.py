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
- home_temperature, night_temperature, away_temperature, vacation_temperature, motion_temperature: numeric targets.
- *_temperature_control: optional entity ids (number/select) used to change the respective temperature via UI.
- aqi_sensor, voc_sensor, co2_sensor: optional air-quality sensors and thresholds (aqi_threshold, voc_threshold, co2_threshold).
- summer_temperature_threshold, summer_temperature: thresholds and target for summer behavior.
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
    home_temperature: 21
    away_temperature: 17
    vacation_temperature: 15
```

See module docstring and inline examples for usage.
"""

import appdaemon.plugins.hass.hassapi as hass
from base import BaseApp
from datetime import datetime, timezone
import inspect



class ClimateControl(BaseApp):

    def initialize(self):
        super().initialize()
        self.log("Hello from ClimateControl")

        # setup sane defaults
        self._climate_controls = self.args.get("climate_controls", [])

        self._external_temperature_sensor = self.args.get("external_temperature_sensor", None)
        self._outside_temperature_sensor = self.args.get("outside_temperature_sensor", None)
        self._max_overheat_allowance = self.args.get("max_overheat_allowance", 0.5)
        self._fan_overheat_temperature = float(self.args.get("fan_overheat_temperature", 22))
        self._summer_temperature_threshold = float(self.args.get("summer_temperature_threshold", 15))
        self._summer_temperature_threshold_tomorrow = float(self.args.get("summer_temperature_threshold_tomorrow", self._summer_temperature_threshold + 3))

        self._min_temperature = float(self.args.get("min_temperature", 7))

        self._aqi_sensor = self.args.get("aqi_sensor", None)
        self._aqi_threshold = int(self.args.get("aqi_threshold", 50))

        self._voc_sensor = self.args.get("voc_sensor", None)
        self._voc_threshold = int(self.args.get("voc_threshold", 220))

        self._co2_sensor = self.args.get("co2_sensor", None)
        self._co2_threshold = int(self.args.get("co2_threshold", 800))

        self._humidity_sensor = self.args.get("humidity_sensor", None)

        self._offset_temperature = float(self.args.get("offset_temperature", 0))
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
        self._summer_temperature = float(self.args.get("summer_temperature", 7))
        self._summer_hvac_mode = self.args.get("summer_hvac_mode", "off")
        self._summer_temperature_control = self.args.get("summer_temperature_control", None)

        self.log("=== Climate Control Configuration ===")
        self.log(f"Climate controls: {self._climate_controls}")
        self.log(f"External temperature sensor: {self._external_temperature_sensor}")
        self.log(f"Outside temperature sensor: {self._outside_temperature_sensor}")
        self.log(f"Offset temperature: {self._offset_temperature}")
        self.log(f"Max overheat allowance: {self._max_overheat_allowance}")
        self.log(f"Fan overheat temperature: {self._fan_overheat_temperature}°C")
        self.log(f"Minimum temperature: {self._min_temperature}°C")

        self.log("--- Air Quality Sensors ---")
        self.log(f"AQI sensor: {self._aqi_sensor}, threshold: {self._aqi_threshold}")
        self.log(f"VOC sensor: {self._voc_sensor}, threshold: {self._voc_threshold}")
        self.log(f"CO₂ sensor: {self._co2_sensor}, threshold: {self._co2_threshold}")

        self.log("--- Seasonal Settings ---")
        self.log(f"Summer temperature threshold (today): {self._summer_temperature_threshold}°C")
        self.log(f"Summer temperature threshold (tomorrow): {self._summer_temperature_threshold_tomorrow}°C")
        self.log(f"Summer mode: {self._summer_hvac_mode}, target: {self._summer_temperature}°C (control: {self._summer_temperature_control})")

        self.log("--- Temperature Modes ---")
        self.log(f"Home: {self.get_desired_temperature_by_status('home')}°C, HVAC: {self._home_hvac_mode}, Control: {self._home_temperature_control}")
        self.log(f"Night: {self.get_desired_temperature_by_status('night')}°C, HVAC: {self._night_hvac_mode}, Control: {self._night_temperature_control}")
        self.log(f"Away: {self.get_desired_temperature_by_status('away')}°C HVAC: {self._away_hvac_mode}, Control: {self._away_temperature_control}")
        self.log(f"Vacation: {self.get_desired_temperature_by_status('vacation')}°C, HVAC: {self._vacation_hvac_mode}, Control: {self._vacation_temperature_control}")
        self.log(f"Open-window: {self.get_desired_temperature_by_status('open')}°C, HVAC: {self._open_hvac_mode}, Control: {self._open_temperature_control}")
        self.log(f"Motion: {self.get_desired_temperature_by_status('motion')}°C, HVAC: {self._motion_hvac_mode}, Duration: {self._motion_duration}s, Control: {self._motion_temperature_control}")

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
                                new="on", old="off", duration=self._motion_timeout)

        # change based on settings in gui
        for temptype in ['home', 'away', 'vacation', 'open', 'motion', 'night']:
            if vars(self)['_' + temptype + '_temperature_control'] is None:
                continue
            self.log(f"Listening for {vars(self)['_' + temptype + '_temperature_control']}")
            self.listen_state(self.sensor_change_callback, vars(self)['_' + temptype + '_temperature_control'] )

        # change based on climate control
        for climate_control in self._climate_controls:
            # record changes
            self.listen_state(self.control_change_callback, climate_control)
            self.listen_state(self.control_change_callback, climate_control, attribute="temperature")
            self.listen_state(self.control_change_callback, climate_control, attribute="hvac_mode")
            self.listen_state(self.control_change_callback, climate_control, attribute="fan_mode")
            self.listen_state(self.control_change_callback, climate_control, attribute="preset_mode")
            self.listen_state(self.control_change_callback, climate_control, attribute="swing_mode")
            self.listen_state(self.control_change_callback, climate_control, attribute="swing_horizontal_mode")
            # act on changes delayed
            self.listen_state(self.sensor_change_callback, climate_control, duration=60)
            self.listen_state(self.sensor_change_callback, climate_control, attribute="temperature", duration=60)
            self.listen_state(self.sensor_change_callback, climate_control, attribute="hvac_mode", duration=60)
            self.listen_state(self.sensor_change_callback, climate_control, attribute="fan_mode", duration=60)
            self.listen_state(self.sensor_change_callback, climate_control, attribute="preset_mode", duration=60)

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
        if self.get_external_temperature() == None:
            return False

        if self.get_external_temperature() > self.get_desired_temperature() + self._max_overheat_allowance:
            return True
        
        return False

    def is_cooling(self, entity_id):
        if self.get_current_hvac_mode(entity_id) == 'cool':
            return True
        
        return False

    def is_summer(self):
        if self.get_outside_temperature() > self._summer_temperature_threshold:
            return True
        if self.get_max_outside_temperature_today() > self._summer_temperature_threshold:
            return True
        if self.get_max_outside_temperature_tomorrow() > self._summer_temperature_threshold_tomorrow:
            return True
        return False

    def is_aqi_okay(self):
        value_sensor = self.get_aqi_measurement()
        if value_sensor == None:
            return True

        if int(value_sensor) > self._aqi_threshold:
            return False

        return True

    def is_voc_okay(self):
        value_sensor = self.get_voc_measurement()
        if value_sensor == None:
            return True

        if int(value_sensor) > self._voc_threshold:
            return False

        return True

    def is_co2_okay(self):
        value_sensor = self.get_co2_measurement()
        if value_sensor == None:
            return True

        if int(value_sensor) > self._co2_threshold:
            return False

        return True

    def in_guest_mode(self):
        if self._guest_control is None:
            return False
        if self.get_state(self._guest_control) == 'on':
            return True
        else:
            return False

    def in_vacation_mode(self):
        if self._vacation_control is None:
            return False
        if self.get_state(self._vacation_control) == 'on':
            return True
        else:
            return False

    def get_current_status(self):
        if(self.is_summer()):
            return "summer"
        elif(self.count_on_opening_sensors() > 0):
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
        if self._aqi_sensor == None:
            return None

        value_sensor = self.get_state(self._aqi_sensor)
        if value_sensor == 'unknown':
            return None
        if value_sensor == 'unavailable':
            return None

        return int(value_sensor)

    def get_voc_measurement(self):
        if self._voc_sensor == None:
            return None

        value_sensor = self.get_state(self._voc_sensor)
        if value_sensor == 'unknown':
            return None
        if value_sensor == 'unavailable':
            return None

        return int(value_sensor)

    def get_co2_measurement(self):
        if self._co2_sensor == None:
            return None

        value_sensor = self.get_state(self._co2_sensor)
        if value_sensor == 'unknown':
            return None
        if value_sensor == 'unavailable':
            return None

        return int(value_sensor)

    def get_humidity_measurement(self):
        if self._humidity_sensor == None:
            return None

        value_sensor = self.get_state(self._humidity_sensor)
        if value_sensor == 'unknown':
            return None
        if value_sensor == 'unavailable':
            return None

        return float(value_sensor)

    def get_external_temperature(self):
        if self._external_temperature_sensor == None:
            return None

        value_sensor = self.get_state(self._external_temperature_sensor)
        if value_sensor == 'unknown':
            return None
        if value_sensor == 'unavailable':
            return None

        return float(value_sensor)

    def get_outside_temperature(self):
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

        if value_forecast == None:
            return 0

        return float(value_forecast)

    def get_max_outside_temperature_today(self):
        value = self.get_state('sensor.temperature_max_today')
        if value == None:
            return 0
        if value == 'unknown':
            return 0
        if value == 'unavailable':
            return 0
        return float(value)

    def get_max_outside_temperature_tomorrow(self):
        value = self.get_state('sensor.temperature_max_tomorrow')
        if value == None:
            return 0
        if value == 'unknown':
            return 0
        if value == 'unavailable':
            return 0
        return float(value)

    def get_desired_temperature_by_status(self, status):
        if vars(self)['_' + status + '_temperature_control'] is None:
            self.log(f"{'self._' + status + '_temperature_control'} is None", level="DEBUG")
            if vars(self)['_' + status + '_temperature'] is None:
                self.log(f"{'self._' + status + '_temperature'} is None", level="DEBUG")
                return None
            return float(vars(self)['_' + status+ '_temperature']) + float(self._offset_temperature)
        else:
            return float(self.get_state(vars(self)['_' + status + '_temperature_control'])) + float(self._offset_temperature)

    def get_desired_temperature(self):
        desired_temp = self.get_desired_temperature_by_status(self.get_current_status())
        if desired_temp is None:
            return self._min_temperature
        return float(max(desired_temp, self._min_temperature))

    def get_desired_hvac_mode_by_status(self, status):
        return vars(self)['_' + status + '_hvac_mode']

    def get_desired_hvac_mode(self, entity_id = None):
        desired_mode = self.get_desired_hvac_mode_by_status(self.get_current_status())

        fan_supported = False
        if entity_id is not None:
            fan_supported = self.is_fan_mode_supported(entity_id, 'Auto')

        if self.is_overheating():
            if (
                fan_supported
                and self.is_somebody_at_home()
                and self.count_on_opening_sensors() == 0
                and self.get_external_temperature() > self._fan_overheat_temperature
                and not self.is_summer()
                and not self.is_time_in_night_window()
            ):              
                desired_mode = 'fan_only'
            else:
                desired_mode = 'off'
            self.log(f"Setting desired hvac mode to off {desired_mode} to overheat", level="DEBUG")

        if desired_mode == 'off' and fan_supported:
            if (self.is_aqi_okay() == False or self.is_voc_okay() == False):
                if (self.is_somebody_at_home() and self.count_on_opening_sensors() == 0):
                    self.log("Setting desired hvac mode to fan_only due to bad air", level="DEBUG")
                    desired_mode = 'fan_only'

        return desired_mode

    def get_current_temperature(self, entity_id):
        value = self.get_state(entity_id, attribute = "current_temperature")
        if value == None:
            return 0
        if value == 'unknown':
            return 0
        if value == 'unavailable':
            return 0
        return float(value)

    def get_target_temperature(self, entity_id):
        value = self.get_state(entity_id, attribute = "temperature")
        if value == None:
            return 0
        if value == 'unknown':
            return 0
        if value == 'unavailable':
            return 0
        return float(value)

    def get_current_fan_mode(self, entity_id):
        return self.get_state(entity_id, attribute = "fan_mode")

    def get_desired_fan_mode(self, entity_id = None):
        desired_mode = "Auto"

        if entity_id is not None:
            if not self.is_fan_mode_supported(entity_id, 'Auto'):
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
        if self.get_desired_fan_mode() == None:
            self.log(f"[{entity_id}] Cannot set optimal fan mode: Desired setting is None.", level="ERROR")
            return

        if self.is_summer() and self.is_cooling(entity_id):
            self.log(f"[{entity_id}] Cannot set optimal fan mode: Device is cooling during summer.")
            return

        if self.get_current_fan_mode(entity_id) == self.get_desired_fan_mode():
            self.log(f"[{entity_id}] Optimal fan mode is already set.")
            return

        if not self.is_fan_mode_supported(entity_id, self.get_desired_fan_mode(entity_id)):
            self.log(f"[{entity_id}] Cannot set optimal fan mode: Device does not support fan mode {self.get_desired_fan_mode(entity_id)}.", level="ERROR")
            return

        self.set_fan_mode(entity_id, self.get_desired_fan_mode(entity_id))

    def get_current_preset_mode(self, entity_id):
        return self.get_state(entity_id, attribute = "preset_mode")

    def get_desired_preset_mode(self, entity_id = None):
        desired_mode = "quiet"

        if entity_id is not None:
            if not self.is_preset_mode_supported(entity_id, 'quiet'):
                return None

        return desired_mode

    def set_optimal_preset_mode(self, entity_id):
        if self.get_desired_preset_mode() == None:
            self.log(f"[{entity_id}] Cannot set optimal preset mode: Desired setting is None.")
            return

        if self.is_summer() and self.is_cooling(entity_id):
            self.log(f"[{entity_id}] Cannot set optimal preset mode: Device is cooling during summer.")
            return

        if self.get_current_preset_mode(entity_id) == self.get_desired_preset_mode():
            self.log(f"[{entity_id}] Optimal preset mode is already set.")
            return

        if not self.is_preset_mode_supported(entity_id, self.get_desired_preset_mode(entity_id)):
            self.log(f"[{entity_id}] Cannot set optimal preset mode: Device does not support preset mode {self.get_desired_preset_mode(entity_id)}.", level="ERROR")
            return

        self.set_preset_mode(entity_id, self.get_desired_preset_mode(entity_id))

    def get_current_hvac_mode(self, entity_id):
        return self.get_state(entity_id)

    def set_optimal_hvac_mode(self, entity_id):
        if self.get_desired_hvac_mode() == None:
            self.log(f"[{entity_id}] Cannot set optimal hvac mode: Desired setting is None.", level="ERROR")
            return

        if self.is_summer() and self.is_cooling(entity_id):
            self.log(f"[{entity_id}] Cannot set optimal hvac mode: Device is cooling during summer.")
            return

        if self.get_current_hvac_mode(entity_id) == self.get_desired_hvac_mode(entity_id):
            self.log(f"[{entity_id}] Optimal hvac mode is already set.")
            return

        self.set_hvac_mode(entity_id, self.get_desired_hvac_mode(entity_id))

    def set_optimal_temperature(self, entity_id):
        if self.get_desired_temperature() == None:
            self.log(f"[{entity_id}] Cannot set optimal temperature: Desired temperature is None.", level="ERROR")
            return

        if self.is_summer() and self.is_cooling(entity_id):
            self.log(f"[{entity_id}] Cannot set optimal temperature: Device is cooling during summer.")
            return

        if self.get_desired_hvac_mode(entity_id) == 'off':
            self.log(f"[{entity_id}] Cannot set optimal temperature: Desired hvac mode is off.")
            return

        # if self.is_overheating():
        #     self.log(f"[{entity_id}] Cannot set optimal temperature: Room is overheating.")
        #     return

        if self.get_target_temperature(entity_id) == self.get_desired_temperature():
            self.log(f"[{entity_id}] Optimal temperature is already set.")
            return

        self.set_temperature(entity_id, self.get_desired_temperature())

    def periodic_time_callback(self, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name}")

        self.update_climate()

    def control_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        if self.is_current_change_external():
            if attribute == 'temperature' and new == self.get_desired_temperature():
                self.log("Ignoring externl change because it matches the desired temperature")
                return
            if attribute == 'temperature' and new == self._min_temperature and self.get_current_hvac_mode(entity) == 'off':
                self.log("Ignoring externl change because it matches expected temperature for hvac mode moff")
                return
            if attribute == 'hvac_mode' and new == self.get_desired_hvac_mode(entity):
                self.log("Ignoring externl change because it matches the desired hvac mode")
                return
            if attribute == 'fan_mode' and new == self.get_desired_fan_mode(entity):
                self.log("Ignoring externl change because it matches the desired fan mode")
                return
            if attribute == 'preset_mode' and new == self.get_desired_preset_mode(entity):
                self.log("Ignoring externl change because it matches the desired preset mode")
                return

        super().control_change_callback(entity, attribute, old, new, kwargs)

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        self.update_climate()

    def update_climate(self):
        self.log("=== Updating climate controls ===")
        
        # Status and temperature overview
        self.log(f"Status: {self.get_current_status()} | External: {self.get_external_temperature()}°C | Outside: {self.get_outside_temperature()}°C | Max today/tomorrow: {self.get_max_outside_temperature_today()}°C/{self.get_max_outside_temperature_tomorrow()}°C")
        
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
            self.log(f"[{climate_control}] Temp: {self.get_current_temperature(climate_control)}°C (current) | {self.get_target_temperature(climate_control)}°C (target) | {self.get_desired_temperature()}°C (desired)")

            # HVAC mode status
            self.log(f"[{climate_control}] HVAC: {self.get_current_hvac_mode(climate_control)} (current) → {self.get_desired_hvac_mode(climate_control)} (desired)")

            # Fan and preset modes (only if supported)
            mode_info = []
            if self.is_fan_mode_supported(climate_control):
                mode_info.append(f"Fan: {self.get_current_fan_mode(climate_control)} → {self.get_desired_fan_mode(climate_control)}")
            if self.is_preset_mode_supported(climate_control):
                mode_info.append(f"Preset: {self.get_current_preset_mode(climate_control)} → {self.get_desired_preset_mode(climate_control)}")
            
            if mode_info:
                self.log(f"[{climate_control}] {' | '.join(mode_info)}")

            if(self.is_internal_change_allowed()):
                self.set_optimal_temperature(climate_control)
                self.set_optimal_hvac_mode(climate_control)
                if self.is_fan_mode_supported(climate_control):
                    self.set_optimal_fan_mode(climate_control)
                if self.is_preset_mode_supported(climate_control):
                    self.set_optimal_preset_mode(climate_control)
            else:
                remaining_seconds = self.get_remaining_seconds_before_internal_change_is_allowed()
                self.log(f"[{climate_control}] Doing nothing: Internal change is not allowed for {remaining_seconds:.2f} more seconds.")


    def set_temperature(self, entity_id, temperature):
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
        self.log(f"[{entity_id}] Changing hvac_mode from {self.get_current_hvac_mode(entity_id)} to {hvac_mode}")

        if hvac_mode is None:
            self.error(f"[{entity_id}] Cannot set hvac_mode to None", level="ERROR")
            return

        if self.is_hvac_mode_supported(entity_id, hvac_mode) == False:
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
        fan_modes = self.get_state(entity_id, attribute='fan_modes')
        self.log(f"[{entity_id}] Got fan modes: {fan_modes}", level="DEBUG")
        if fan_modes is None:
            return False
        if fan_mode is None:
            return True
        self.log(f"[{entity_id}] Fan mode {fan_mode} in valid fan modes {fan_modes}: {fan_mode in fan_modes}", level="DEBUG")
        return fan_mode in fan_modes

    def set_fan_mode(self, entity_id, fan_mode = 'Auto'):
        self.log(f"[{entity_id}] Changing fan_mode from {self.get_current_fan_mode(entity_id)} to {fan_mode}")

        if fan_mode is None:
            self.error(f"[{entity_id}] Cannot set fan_mode to None", level="ERROR")
            return

        if self.is_fan_mode_supported(entity_id, fan_mode) == False:
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
        preset_modes = self.get_state(entity_id, attribute='preset_modes')
        self.log(f"[{entity_id}] Got preset modes: {preset_modes}", level="DEBUG")
        if preset_modes is None:
            return False
        if preset_mode is None:
            return True
        self.log(f"[{entity_id}] preset mode {preset_mode} in valid preset modes {preset_modes}: {preset_mode in preset_modes}", level="DEBUG")
        return preset_mode in preset_modes

    def set_preset_mode(self, entity_id, preset_mode = 'none'):
        self.log(f"[{entity_id}] Changing preset_mode from {self.get_current_preset_mode(entity_id)} to {preset_mode}")

        if preset_mode is None:
            self.error(f"[{entity_id}] Cannot set preset_mode to None", level="ERROR")
            return

        if self.is_preset_mode_supported(entity_id, preset_mode) == False:
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