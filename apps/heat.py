import appdaemon.plugins.hass.hassapi as hass

#
# HeatSaver App
#
# Args:
#


class HeatSaver(hass.Hass):

    def initialize(self):
        self.log("Hello from HeatSaver")

        # setup sane defaults
        self._door_window_sensors = self.args.get("door_window_sensors", [])
        self._device_trackers = self.args.get("device_trackers", [])
        self._motion_sensors = self.args.get("motion_sensors", [])
        self._climate_controls = self.args.get("climate_controls", [])
        self._vacation_control = self.args.get("vacation_control", None)
        self._guest_control = self.args.get("guest_control", None)
        self._wait_duration = self.args.get("wait_duration", 15)
        self._external_temperature_sensor = self.args.get("external_temperature_sensor", None)
        self._max_overheat_allowance = self.args.get("max_overheat_allowance", 1)

        # todo
        self._offset_temperature = self.args.get("offset_temperature", 0)
        self._motion_temperature = self.args.get("motion_temperature", 21)
        self._motion_temperature_control = self.args.get("motion_temperature_control", None)
        self._motion_hvac_mode = self.args.get("motion_hvac_mode", "heat")
        self._motion_timeout = self.args.get("motion_timeout", 300)
        self._home_temperature = self.args.get("home_temperature", 20)
        self._home_temperature_control = self.args.get("home_temperature_control", None)
        self._home_hvac_mode = self.args.get("home_hvac_mode", "heat")
        self._night_temperature = self.args.get("night_temperature", 18)
        self._night_temperature_control = self.args.get("night_temperature_control", None)
        self._night_hvac_mode = self.args.get("night_hvac_mode", "heat")
        self._away_temperature = self.args.get("away_temperature", 18)
        self._away_temperature_control = self.args.get("away_temperature_control", None)
        self._away_hvac_mode = self.args.get("away_hvac_mode", "heat")
        self._vacation_temperature = self.args.get("vacation_temperature", 16)
        self._vacation_hvac_mode = self.args.get("vacation_hvac_mode", "heat")
        self._vacation_temperature_control = self.args.get("vacation_temperature_control", None)
        self._open_temperature = self.args.get("open_temperature", 14)
        self._open_hvac_mode = self.args.get("open_hvac_mode", "off")
        self._open_temperature_control = self.args.get("open_temperature_control", None)
        self._overheat_hvac_mode = self.args.get("overheat_hvac_mode", "off")
        self._summer_temperature = self.args.get("summer_temperature", None)
        self._summer_hvac_mode = self.args.get("summer_hvac_mode", "off")
        self._summer_temperature_control = self.args.get("summer_temperature_control", None)

        # sleep time
        self._night_after_time = self.args.get("night_after_time", "22:00:00")
        self._night_before_time = self.args.get("night_before_time", "07:00:00")

        # log current config
        self.log("Got door and window sensors {}".format(
            self._door_window_sensors))
        self.log("Got device trackers {}".format(self._device_trackers))
        self.log("Got motion sensors {}".format(self._motion_sensors))
        self.log("Got climate controls {}".format(self._climate_controls))
        self.log("Got wait duration {}".format(self._wait_duration))
        self.log("Got offset temperature {}".format(self._offset_temperature))
        self.log("Got {} device_trackers home and {} device_trackers not home".format(
            self.count_home_device_trackers(), self.count_not_home_device_trackers()))
        self.log("Got guest_mode {}".format(self.in_guest_mode()))
        self.log("Got vacation_mode {}".format(self.in_vacation_mode()))
        self.log("Got current_status {}".format(self.get_current_status()))
        for temptype in ['home', 'away', 'vacation', 'open', 'motion', 'night']:
            self.log("Got desired_temperature for status {}: {}".format(temptype,
                self.get_desired_temperature_by_status(temptype)))
            self.log("Got desired_hvac_mode for status {}: {}".format(temptype,
                self.get_desired_hvac_mode_by_status(temptype)))

        # stop heating if doors or windows are open
        for sensor in self._door_window_sensors:
            self.listen_state(self.change_heater_callback, sensor,
                              new="on", old="off", duration=self._wait_duration)
            self.listen_state(self.change_heater_callback,
                              sensor, new="off", old="on")

        # stop heating if nobody is home
        for sensor in self._device_trackers:
            self.listen_state(self.change_heater_callback, sensor,
                              new="not_home", old="home", duration=self._wait_duration)
            self.listen_state(self.change_heater_callback,
                              sensor, new="home", old="not_home")

        # stop heating during vacation
        if self._vacation_control is not None:
            self.listen_state(self.change_heater_callback, self._vacation_control,
                              new="on", old="off", duration=self._wait_duration)
            self.listen_state(self.change_heater_callback,
                              self._vacation_control, new="off", old="on")

        # start heating for guests
        if self._guest_control is not None:
            self.listen_state(self.change_heater_callback,
                              self._guest_control, new="on", old="off")
            self.listen_state(self.change_heater_callback,
                              self._guest_control, new="off", old="on")

        # start heating for motion events
        for sensor in self._motion_sensors:
            self.listen_state(self.change_heater_callback, sensor,
                              new="off", old="on", duration=self._motion_timeout)
            self.listen_state(self.change_heater_callback, sensor,
                              new="on", old="off")

        # change based on settings in gui
        for temptype in ['home', 'away', 'vacation', 'open', 'motion', 'night']:
            if vars(self)['_' + temptype + '_temperature_control'] is None:
                continue
            self.log("Listening for {}".format(vars(self)['_' + temptype + '_temperature_control']))
            self.listen_state(self.change_heater_callback, vars(self)['_' + temptype + '_temperature_control'] )

        # change based on climate control
        for climate_control in self._climate_controls:
            self.listen_state(self.change_heater_callback,
                              climate_control, new="auto", old="manual")

        # listen for time changes
        if(self._night_after_time is not None):
            runtime = self.parse_time(self._night_after_time)
            self.run_daily(self.night_auto_timer_callback, runtime)
            self.log("Got night_after_time {}".format(runtime))
        if(self._night_before_time is not None):
            runtime = self.parse_time(self._night_before_time)
            self.run_daily(self.night_auto_timer_callback, runtime)
            self.log("Got night_before_time {}".format(runtime))

        if self._external_temperature_sensor:
            self.listen_state(self.change_heater_callback, self._external_temperature_sensor)

        self.listen_state(self.change_heater_callback, 'weather.forecast_home')

        # initial setup
        self.update_heater()


    def count_doors_and_windows(self, state):
        count = 0
        for sensor in self._door_window_sensors:
            if self.get_state(sensor) == state:
                count = count + 1
        return count

    def count_open_doors_and_windows(self):
        return self.count_doors_and_windows("on")

    def count_closed_doors_and_windows(self):
        return self.count_doors_and_windows("off")

    def count_device_trackers(self, state):
        count = 0
        for sensor in self._device_trackers:
            if self.get_state(sensor) == state:
                count = count + 1
        return count

    def count_home_device_trackers(self):
        return self.count_device_trackers("home")

    def count_not_home_device_trackers(self):
        return self.count_device_trackers("not_home")

    def count_motion_sensors(self, state):
        count = 0
        for sensor in self._motion_sensors:
            if self.get_state(sensor) == state:
                count = count + 1
        return count

    def count_on_motion_sensors(self):
        return self.count_motion_sensors("on")

    def count_off_motion_sensors(self):
        return self.count_motion_sensors("off")

    def is_time_in_night_window(self):
        # self.log(self._night_after_time)
        # self.log(self._night_before_time)
        return self.now_is_between(self._night_after_time, self._night_before_time)

    def is_overheating(self):
        if self._external_temperature_sensor == None:
            return False

        if self.get_external_temperature() > self.get_desired_temperature() + self._max_overheat_allowance:
            return True

    def is_cooling(self, entity_id):
        if self.get_current_hvac_mode(entity_id) == 'cool':
            return True

    def is_summer(self):
        if self.get_outside_temperature() > 18:
            return True
        return False

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
        elif(self.count_open_doors_and_windows() > 0):
            return "open"
        elif(self.in_vacation_mode()):
            return "vacation"
        elif(self.is_time_in_night_window()):
            return "night"
        elif(self.count_on_motion_sensors() > 0):
            return "motion"
        elif(self.in_guest_mode()):
            return "home"
        elif(self.count_home_device_trackers() == 0):
            return "away"
        return "home"

    def get_external_temperature(self):
        if self._external_temperature_sensor == None:
            return False
        return float(self.get_state(self._external_temperature_sensor))

    def get_outside_temperature(self):
        value = self.get_state('weather.forecast_home', attribute = "temperature")
        if value == None:
            return 0
        if value == 'unknown':
            return 0
        if value == 'unavailable':
            return 0
        return float(value)

    def get_desired_temperature_by_status(self, status):
        if vars(self)['_' + status + '_temperature_control'] is None:
            if vars(self)['_' + status + '_temperature'] is None:
                return None
            return float(vars(self)['_' + status+ '_temperature']) + float(self._offset_temperature)
        else:
            return float(self.get_state(vars(self)['_' + status + '_temperature_control'])) + float(self._offset_temperature)

    def get_desired_temperature(self):
        return self.get_desired_temperature_by_status(self.get_current_status())

    def get_desired_hvac_mode_by_status(self, status):
        return vars(self)['_' + status + '_hvac_mode']

    def get_desired_hvac_mode(self):
        return self.get_desired_hvac_mode_by_status(self.get_current_status())

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

    def get_current_hvac_mode(self, entity_id):
        return self.get_state(entity_id)

    def set_optimal_hvac_mode(self, entity_id):
        if self.get_desired_hvac_mode() == None:
            self.log("Cannot set hvac_mode because setting is None")
            return

        if self.is_summer() and self.is_cooling(entity_id):
            self.log("Cannot set hvac_mode because it is summer and device is cooling")
            return

        if self.is_overheating():
            self.log("Heater {} is overheating setting hvac_mode {}".format(
                entity_id, self.get_desired_hvac_mode_by_status("overheat")))
            self.set_hvac_mode(entity_id, self.get_desired_hvac_mode_by_status("overheat"))

            return

        self.set_hvac_mode(entity_id, self.get_desired_hvac_mode())


    def set_optimal_temperature(self, entity_id):
        if self.get_desired_temperature() == None:
            self.log("Cannot set temperature because setting is None")
            return

        if self.is_summer() and self.is_cooling(entity_id):
            self.log("Cannot set temperature because it is summer and device is cooling")
            return

        self.set_temperature(entity_id, self.get_desired_temperature())


    def night_auto_timer_callback(self, kwargs):
        self.log("Night auto timer callback")

        self.log("Current status is {}".format(self.get_current_status()))

        self.log("Current external temperature is {}".format(self.get_external_temperature()))
        self.log("Current outside temperature is {}".format(self.get_outside_temperature()))
        self.log("Desired hvac_mode is {}".format(self.get_desired_hvac_mode()))
        self.log("Desired temperature is {}".format(self.get_desired_temperature()))

        self.update_heater()

    def change_heater_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback change_heater from {}:{} {}->{}".format(entity, attribute, old, new))

        self.update_heater()

    def update_heater(self):
        self.log("Current status is {}".format(self.get_current_status()))

        self.log("Current external temperature is {}".format(self.get_external_temperature()))
        self.log("Current outside temperature is {}".format(self.get_outside_temperature()))
        self.log("Desired hvac_mode is {}".format(self.get_desired_hvac_mode()))
        self.log("Desired temperature is {}".format(self.get_desired_temperature()))

        for climate_control in self._climate_controls:
            self.log("Current target temperature is {} at heater {}".format(self.get_target_temperature(climate_control), climate_control))
            self.log("Current internal temperature is {} at heater {}".format(self.get_current_temperature(climate_control), climate_control))
            self.set_optimal_hvac_mode(climate_control)
            self.set_optimal_temperature(climate_control)

    def set_temperature(self, entity_id, temperature):
        self.log("Changing heater {} temperature from {} to {}".format(
            entity_id, self.get_target_temperature(entity_id), temperature))

        if self.get_target_temperature(entity_id) == temperature:
            self.log("Heater {} is already at temperature {}".format(
                entity_id, temperature))
            return

        if temperature is None:
            self.error("Cannot change heater {} temperature to None".format(entity_id))
            return

        self.call_service("climate/set_temperature",
                            entity_id=entity_id, temperature=temperature)

    def set_hvac_mode(self, entity_id, hvac_mode):
        self.log("Changing heater {} hvac_mode from {} to {}".format(
            entity_id, self.get_current_hvac_mode(entity_id), hvac_mode))

        if self.get_current_hvac_mode(entity_id) == hvac_mode:
            self.log("Heater {} is already in hvac_mode {}".format(
                entity_id, hvac_mode))
            return

        if hvac_mode is None:
            self.error("Cannot change heater {} hvac_mode to None".format(entity_id))
            return

        self.call_service("climate/set_hvac_mode",
                        entity_id=entity_id, hvac_mode=hvac_mode)

