import appdaemon.plugins.hass.hassapi as hass

#
# HeatSaver App
#
# Args:
#
# Concept:
# PowerOn if motion
# PowerOff if no motion for motion_duration
# PowerOff if vacation for vacation_duration
# PowerOff if nobody at home for tracker_duration unless guest
# Nothing on startup

class PowerSaver(hass.Hass):

    def initialize(self):
        self.log("Hello from PowerSaver")

        # setup sane defaults
        self._motion_sensors = self.args.get("motion_sensors", [])
        self._device_trackers = self.args.get("device_trackers", [])
        self._power_controls = self.args.get("power_controls", [])
        self._standby_sensors = self.args.get("standby_sensors", [])
        self._vacation_control = self.args.get("vacation_control", None)
        self._guest_control = self.args.get("guest_control", None)
        self._motion_duration = self.args.get("motion_duration", 60*60*2)
        self._tracker_duration = self.args.get("tracker_duration", 60*15)
        self._vacation_duration = self.args.get("vacation_duration", 60)
        self._night_start = self.args.get("night_start", "01:30:00")
        self._night_end = self.args.get("night_end", "06:30:00")
        self._night_force_off = self.args.get("night_force_off", True)

        self._standby_power_limit = self.args.get("standby_power_limit", 0)
        self._standby_power_limit_last_seen = self.args.get("standby_power_limit", None)

        # log current config
        self.log("Got motion sensors {}".format(
            self._motion_sensors))
        self.log("Got device trackers {}".format(self._device_trackers))
        self.log("Got device controls {}".format(self._power_controls))
        self.log("Got motion duration {}".format(self._motion_duration))
        self.log("Got tracker duration {}".format(self._tracker_duration))
        self.log("Got vacation duration {}".format(self._vacation_duration))
        self.log("Got {} device_trackers home and {} device_trackers not home".format(
            self.count_home_device_trackers(), self.count_not_home_device_trackers()))
        self.log("Got guest_mode {}".format(self.in_guest_mode()))
        self.log("Got vacation_mode {}".format(self.in_vacation_mode()))

        # start or stop power based on motion
        for sensor in self._motion_sensors:
            self.listen_state(self.power_on_callback, sensor,
                              new="on", old="off")
            self.listen_state(self.power_off_motion_callback,
                              sensor, new="off", old="on", duration=self._motion_duration)

        # stop power if nobody is home
        for sensor in self._device_trackers:
            self.listen_state(self.power_off_presence_callback,
                              sensor, new="not_home", old="home", duration=self._tracker_duration)

        # stop power during vacation
        if self._vacation_control is not None:
            self.listen_state(self.power_off_presence_callback, self._vacation_control,
                              new="on", old="off", duration=self._vacation_duration)

        # stop power each night
        runtime = self.parse_time(self._night_start)
        self.run_daily(self.power_off_auto_timer_callback, runtime)

        # force stop power at night
        if self._night_force_off:
            for sensor in self._power_controls:
                self.listen_state(self.power_off_force_callback, sensor,
                                new="on", old="off")

    def count_motion_sensors(self, state):
        count = 0
        for sensor in self._motion_sensors:
            if self.get_state(sensor) == state:
                count = count + 1
            elif self.get_seconds_since_update(sensor) < self._motion_duration:
                count = count + 1
        return count

    def count_on_motion_sensors(self):
        return self.count_motion_sensors("on")

    def count_off_motion_sensors(self):
        return self.count_motion_sensors("off")

    def get_seconds_since_update(self, entity):
        last_updated_str = self.get_state(entity, attribute="last_updated")

        if last_updated_str:
            # Convert ISO string to datetime object
            last_updated = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))

            # Get current time in UTC
            now = datetime.now(timezone.utc)

            # Calculate time difference in seconds
            seconds_elapsed = (now - last_updated).total_seconds()

            self.log(f"{entity} was last updated {seconds_elapsed} seconds ago.", level = "DEBUG")
            return seconds_elapsed
        else:
            self.log(f"Could not retrieve last_updated for {entity}.", level = "DEBUG")
            return None


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

    def count_switches(self, state):
        count = 0
        for sensor in self._power_controls:
            if self.get_state(sensor) == state:
                count = count + 1
        return count

    def count_on_switches(self):
        return self.count_switches("on")

    def count_off_switches(self):
        return self.count_switches("off")

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

    def turn_on_power(self):
        for device_control in self._power_controls:
            self.log("Turning on device {}".format(device_control))
            self.turn_on(device_control)

    def turn_off_power(self):
        for device_control in self._power_controls:
            self.log("Turning off device {}".format(device_control))
            self.turn_off(device_control)

    def power_on_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback power_on from {}:{} {}->{}".format(entity, attribute, old, new))

        if self.now_is_between(self._night_start, self._night_end):
            self.log("Ignoring status {} of {} because night time".format(
                new, entity), level = "DEBUG")
            return

        if(self.count_off_switches() == 0):
            self.log("Ignoring callback because all switches are on", level = "DEBUG")
            return

        self.turn_on_power()

    def power_off_motion_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback power_off_motion from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.count_on_switches() == 0):
            self.log("Ignoring callback because all switches are off", level = "DEBUG")
            return

        if(self.count_on_motion_sensors > 0):
            self.log("Ignoring callback because there is still motion", level = "DEBUG")
            return

        self.turn_off_power()

    def power_off_presence_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback power_off_presence from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.count_home_device_trackers() > 0):
            self.log("Ignoring status {} of {} because {} device_trackers are still at home".format(
                new, entity, self.count_home_device_trackers()), level = "DEBUG")
            return

        if(self.in_guest_mode()):
            self.log("Ignoring status {} of {} because {} we have guests".format(
                new, entity, self.count_home_device_trackers()), level = "DEBUG")
            return

        if(self.count_on_motion_sensors > 0):
            self.log("Ignoring callback because there is still motion", level = "DEBUG")
            return

        self.turn_off_power()

    def power_off_force_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback power_off_night from {}:{} {}->{}".format(entity, attribute, old, new))

        if self.now_is_between(self._night_start, self._night_end) == False:
            self.log("Ignoring status {} of {} because day time".format(
                new, entity), level = "DEBUG")
            return

        self.turn_off_power()

    def power_off_auto_timer_callback(self, kwargs):
        self.log(
            "Callback power_off_auto_timer".format())

        if(self.count_on_switches() == 0):
            self.log("Ignoring callback because all switches are off", level = "DEBUG")
            return

        if(self.count_on_motion_sensors >= 0):
            self.log("Ignoring callback because there is still motion", level = "DEBUG")
            return

        self.turn_off_power()
