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
        self._climate_controls = self.args.get("climate_controls", [])
        self._vacation_control = self.args.get("vacation_control", None)
        self._guest_control = self.args.get("guest_control", None)
        self._wait_duration = self.args.get("wait_duration", 15)

        # todo
        self._offset_temperature = self.args.get("offset_temperature", 0)
        self._home_temperature = self.args.get("home_temperature", 20)
        self._home_temperature_control = self.args.get("home_temperature_control", None)
        self._home_operation_mode = self.args.get("home_operation_mode", "auto")
        self._away_temperature = self.args.get("away_temperature", 18)
        self._away_temperature_control = self.args.get("away_temperature_control", None)
        self._away_operation_mode = self.args.get("away_operation_mode", "manual")
        self._vacation_temperature = self.args.get("vacation_temperature", 16)
        self._vacation_operation_mode = self.args.get(
            "vacation_operation_mode", "manual")
        self._vacation_temperature_control = self.args.get("vacation_temperature_control", None)
        self._open_temperature = self.args.get("open_temperature", 14)
        self._open_operation_mode = self.args.get("open_operation_mode", "manual")
        self._open_temperature_control = self.args.get("open_temperature_control", None)

        # log current config
        self.log("Got door and window sensors {}".format(
            self._door_window_sensors))
        self.log("Got device trackers {}".format(self._device_trackers))
        self.log("Got climate controls {}".format(self._climate_controls))
        self.log("Got wait duration {}".format(self._wait_duration))
        self.log("Got offset temperature {}".format(self._offset_temperature))
        self.log("Got {} device_trackers home and {} device_trackers not home".format(
            self.count_home_device_trackers(), self.count_not_home_device_trackers()))
        self.log("Got guest_mode {}".format(self.in_guest_mode()))
        self.log("Got vacation_mode {}".format(self.in_vacation_mode()))
        self.log("Got currente status {}".format(self.get_current_status()))
        self.log("Got desired_operation_mode {}".format(
            self.get_desired_operation_mode()))
        self.log("Got desired_temperature {}".format(
            self.get_desired_temperature()))

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

        # change based on settings in gui
        for temptype in ['home', 'away', 'vacation', 'open']:
            if vars(self)['_' + temptype + '_temperature_control'] is None:
                continue
            self.log("Listening for {}".format(vars(self)['_' + temptype + '_temperature_control']))
            self.listen_state(self.change_heater_callback, vars(self)['_' + temptype + '_temperature_control'] )

        # initial setup
        for climate_control in self._climate_controls:
            self.listen_state(self.change_heater_callback,
                              climate_control, new="auto", old="manual")
            self.set_operation_mode(climate_control)
            self.set_temperature(climate_control)


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
        if(self.count_open_doors_and_windows() > 0):
            return "open"
        elif(self.in_vacation_mode()):
            return "vacation"
        elif(self.in_guest_mode()):
            return "home"
        elif(self.count_home_device_trackers() == 0):
            return "away"
        return "home"

    def get_desired_temperature(self):
        if vars(self)['_' + self.get_current_status() + '_temperature_control'] is None:
            return float(vars(self)['_' + self.get_current_status() + '_temperature']) + float(self._offset_temperature)
        else:
            return float(self.get_state(vars(self)['_' + self.get_current_status() + '_temperature_control'])) + float(self._offset_temperature)

    def get_desired_operation_mode(self):
        return vars(self)['_' + self.get_current_status() + '_operation_mode']

    def get_current_temperature(self, entity_id):
        return float(self.get_state(entity_id, attribute = "temperature"))

    def get_current_operation_mode(self, entity_id):
        return self.get_state(entity_id, attribute = "operation_mode")

    def set_operation_mode(self, entity_id):
        if self.get_desired_operation_mode() == self.get_current_operation_mode(entity_id):
            self.log("Heater {} is already in operation_mode {}".format(
                entity_id, self.get_desired_operation_mode()))
        else:
            self.log("Changing heater {} operation_mode from {} to {}".format(
                entity_id, self.get_state(entity_id, attribute = "operation_mode"), self.get_desired_operation_mode()))
            self.call_service("climate/set_operation_mode",
                              entity_id=entity_id, operation_mode=self.get_desired_operation_mode())

    def set_temperature(self, entity_id):
        if self.get_desired_temperature() == self.get_current_temperature(entity_id):
            self.log("Heater {} is already at temperature {}".format(
                entity_id, self.get_desired_temperature()))
        elif self.get_desired_operation_mode() == "manual":
            self.log("Changing heater {} temperature from {} to {}".format(
                entity_id, self.get_state(entity_id, attribute = "temperature"), self.get_desired_temperature()))
            self.call_service("climate/set_temperature",
                              entity_id=entity_id, temperature=self.get_desired_temperature())

    def change_heater_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback change_heater from {}:{} {}->{}".format(entity, attribute, old, new))

        self.log("Current status is {}".format(self.get_current_status()))
        self.log("Desired operation_mode is {}".format(self.get_desired_operation_mode()))
        self.log("Desired temperature is {}".format(self.get_desired_temperature()))

        for climate_control in self._climate_controls:
            self.set_operation_mode(climate_control)
            self.set_temperature(climate_control)
