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

class LightSaver(hass.Hass):

    def initialize(self):
        self.log("Hello from LightSaver")

        # setup sane defaults
        self._motion_sensors = self.args.get("motion_sensors", [])
        self._illumination_sensors = self.args.get("illumination_sensors", [])
        self._device_trackers = self.args.get("device_trackers", [])
        self._lights = self.args.get("lights", [])
        self._vacation_control = self.args.get("vacation_control", None)
        self._guest_control = self.args.get("guest_control", None)
        self._motion_duration = self.args.get("motion_duration", 60*3)
        self._tracker_duration = self.args.get("tracker_duration", 60)
        self._vacation_duration = self.args.get("vacation_duration", 60)
        self._min_elevation = self.args.get("min_elevation", 10)
        self._min_illumination = self.args.get("min_illumination", 15)

        self._night_scene = self.args.get("night_scene", None)
        self._evening_scene = self.args.get("evening_scene", None)
        self._off_scene = self.args.get("off_scene", None)
        self._night_start = self.args.get("night_start", "23:15:00")
        self._night_end = self.args.get("night_end", "06:30:00")

        # log current config
        self.log("Got motion sensors {}".format(
            self._motion_sensors))
        self.log("Got device trackers {}".format(self._device_trackers))
        self.log("Got lights {}".format(self._lights))
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

        # start power based on illumination
        for sensor in self._illumination_sensors:
            self.listen_state(self.power_on_callback, sensor)

        # start or stop power based on elevation
        self.listen_state(self.power_on_callback, "sun.sun", attribute = "elevation")

        # stop power if nobody is home
        for sensor in self._device_trackers:
            self.listen_state(self.power_off_presence_callback,
                              sensor, new="home", old="not_home", duration=self._tracker_duration)

        # stop power during vacation
        if self._vacation_control is not None:
            self.listen_state(self.power_off_presence_callback, self._vacation_control,
                              new="on", old="off", duration=self._vacation_duration)

    def count_motion(self, state):
        count = 0
        for sensor in self._motion_sensors:
            if self.get_state(sensor) == state:
                count = count + 1
        return count

    def count_on_motion(self):
        return self.count_motion("on")

    def count_off_motion(self):
        return self.count_motion("off")

    def count_lights(self, state):
        count = 0
        for sensor in self._lights:
            if self.get_state(sensor) == state:
                count = count + 1
        return count

    def count_on_lights(self):
        return self.count_lights("on")

    def count_off_lgihts(self):
        return self.count_motion("off")

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

    def below_min_elevation(self):
        if self.get_state("sun.sun", attribute = "elevation") < self._min_elevation:
            return True
        return False

    def below_min_illumination(self):
        for sensor in self._illumination_sensors:
            #self.log("sensor state {} min ilu {} result {}".format(
            #    self.get_state(sensor), self._min_illumination, self.get_state(sensor) < self._min_illumination))
            if self.get_state(sensor) == 'unavailable':
                return True
            if float(self.get_state(sensor)) < self._min_illumination:
                return True
        return False

    def turn_on_lights(self):
        if self.now_is_between(self._night_start, self._night_end):
            if self._night_scene is not None:
                self.log("Activating scene {}".format(self._night_scene))
                self.turn_on(self._night_scene)
        else:
            if self._evening_scene is not None:
                self.log("Activating scene {}".format(self._evening_scene))
                self.turn_on(self._evening_scene)

    def turn_off_lights(self):
        if self._off_scene is not None:
            self.log("Activating scene {}".format(self._off_scene))
            self.turn_on(self._off_scene)

    def power_on_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback power_on from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.below_min_elevation() == False):
            self.log("Ignoring callback because elevation is still high enough", level = "DEBUG")
            return

        if len(self._illumination_sensors) > 0:
            if(self.below_min_illumination() == False):
                self.log("Ignoring callback because illumination is still high enough", level = "DEBUG")
                return

        if(self.count_on_motion() == 0):
            self.log("Ignoring callback because there is no motion", level = "DEBUG")
            return

        if(self.in_vacation_mode()):
            self.log("Ignoring callback because vacation mode is on", level = "DEBUG")
            return

        if(self.count_on_lights() > 0):
            self.log("Ignoring callback because lights are on", level = "DEBUG")
            return

        self.turn_on_lights()

    def power_off_motion_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback power_off_motion from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.count_on_motion() > 0):
            self.log("Ignoring callback because we still have motion", level = "DEBUG")
            return

        if(self.count_on_lights() == 0):
            self.log("Ignoring callback because lights are off", level = "DEBUG")
            return

        self.turn_off_lights()

    def power_off_presence_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback power_off_presence from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.count_home_device_trackers() > 0):
            self.log("Ignoring callback because {} device_trackers are still at home".format(
                self.count_home_device_trackers()), level = "DEBUG")
            return

        if(self.in_guest_mode()):
            self.log("Ignoring callback because guest mode is on", level = "DEBUG")
            return

        if(self.count_on_lights() == 0):
            self.log("Ignoring callback because lights are off", level = "DEBUG")
            return

        self.turn_off_lights()
