import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, timezone

#
# LightSaver App
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
        self._media_players = self.args.get("media_players", [])

        self._lights = self.args.get("lights", [])
        self._fluxer_switch = self.args.get("fluxer_switch", None)
        self._fluxer_interval = self.args.get("fluxer_interval", 300)
        self._fluxer_handle = None
        self._vacation_control = self.args.get("vacation_control", None)
        self._guest_control = self.args.get("guest_control", None)
        self._alarm_control_panel = self.args.get(
            "alarm_control_panel", "alarm_control_panel.ha_alarm")
        self._motion_duration = self.args.get("motion_duration", 60*5)
        self._tracker_duration = self.args.get("tracker_duration", 60)
        self._vacation_duration = self.args.get("vacation_duration", 60)
        self._min_elevation = self.args.get("min_elevation", 10)
        self._min_illumination = self.args.get("min_illumination", 25)
        self._max_illumination = self.args.get("max_illumination", 150)

        self._night_scene = self.args.get("night_scene", None)
        self._on_scene = self.args.get("on_scene", None)
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
            self.listen_state(self.motion_on_callback, sensor,
                              new="on", old="off")
            self.listen_state(self.motion_off_callback, sensor,
                              new="off", old="on", duration=self._motion_duration)

        for sensor in self._media_players:
            self.listen_state(self.motion_on_callback, sensor,
                              new="on", old="off")

        # stop power if nobody is home
        for sensor in self._device_trackers:
            self.listen_state(self.power_off_presence_callback,
                              sensor, new="not_home", old="home", duration=self._tracker_duration)

        # stop power during vacation
        if self._vacation_control is not None:
            self.listen_state(self.power_off_presence_callback, self._vacation_control,
                              new="on", old="off", duration=self._vacation_duration)

        # start power based on illumination
        for sensor in self._illumination_sensors:
            self.listen_state(self.illumination_change_callback, sensor)

        # start or stop power based on elevation
        self.listen_state(self.elevation_change_callback, "sun.sun", attribute = "elevation")

        if(self.count_on_motion_sensors() == 0):
            self.turn_off_lights()
            self.stop_fluxer()

        if(self.count_on_motion_sensors() > 0 and self.below_min_illumination()):
            self.turn_on_lights()
            self.start_fluxer()

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

    def count_media_players(self, state):
        count = 0
        for sensor in self._media_players:
            if self.get_state(sensor) == state:
                count = count + 1
        return count

    def count_on_media_players(self):
        return self.count_media_players("on")

    def count_off_media_players(self):
        return self.count_media_players("off")

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

    def is_alarm_armed_away(self):
        return self.is_alarm_in_state('armed_away')

    def is_alarm_armed_home(self):
        return self.is_alarm_in_state('armed_home')

    def is_alarm_armed_night(self):
        return self.is_alarm_in_state('armed_night')

    def is_alarm_armed_vacation(self):
        return self.is_alarm_in_state('armed_vacation')

    def is_alarm_disarmed(self):
        return self.is_alarm_in_state('disarmed')

    def is_alarm_pending(self):
        return self.is_alarm_in_state('pending')

    def is_alarm_triggered(self):
        return self.is_alarm_in_state('triggered')

    def is_alarm_in_state(self, state):
        if self._alarm_control_panel is None:
            return False
        if self.get_state(self._alarm_control_panel) == state:
            return True
        else:
            return False

    def get_alarm_state(self):
        if self._alarm_control_panel is None:
            return None
        return self.get_state(self._alarm_control_panel)

    def below_min_elevation(self, value = None):
        if isinstance(value, int) or isinstance(value, float):
            if value < self._min_elevation:
                return True
            return False

        if self.get_state("sun.sun", attribute = "elevation") < self._min_elevation:
            return True
        return False

    def below_min_illumination(self, value = None):
        if isinstance(value, int) or isinstance(value, float):
            if value < self._min_illumination:
                return True
            return False

        for sensor in self._illumination_sensors:
            #self.log("sensor state {} min ilu {} result {}".format(
            #    self.get_state(sensor), self._min_illumination, self.get_state(sensor) < self._min_illumination))
            if self.get_state(sensor) == None:
                return True
            if self.get_state(sensor) == 'unknown':
                return True
            if self.get_state(sensor) == 'unavailable':
                return True
            if float(self.get_state(sensor)) < self._min_illumination:
                return True
        return False

    def above_max_illumination(self, value = None):
        if isinstance(value, int) or isinstance(value, float):
            if value < self._min_illumination:
                return True
            return False

        for sensor in self._illumination_sensors:
            #self.log("sensor state {} min ilu {} result {}".format(
            #    self.get_state(sensor), self._min_illumination, self.get_state(sensor) < self._min_illumination))
            if self.get_state(sensor) == None:
                return False
            if self.get_state(sensor) == 'unknown':
                return False
            if self.get_state(sensor) == 'unavailable':
                return False
            if float(self.get_state(sensor)) > self._max_illumination:
                return True
        return False

    def turn_on_lights(self):
        if(self.count_on_motion_sensors == 0):
            self.log("Ignoring callback because there is no motion", level = "DEBUG")
            return

        if(self.in_vacation_mode()):
            self.log("Ignoring callback because vacation mode is on", level = "DEBUG")
            return

        if(self.is_alarm_triggered() or self.is_alarm_pending()):
            self.log("Ignoring callback because alarm state is {}".format(self.get_alarm_state()), level = "DEBUG")
            return

        if(self.count_on_lights() > 0):
            self.log("Ignoring callback because lights are on", level = "DEBUG")
            return

        if self.now_is_between(self._night_start, self._night_end):
            if self._night_scene is not None:
                self.log("Activating scene {}".format(self._night_scene))
                self.stop_fluxer()
                self.turn_on(self._night_scene)
        else:
            if self._on_scene is not None:
                self.log("Activating scene {}".format(self._on_scene))
                self.start_fluxer()
                self.turn_on(self._on_scene)

    def turn_off_lights(self):
        if(self.count_on_lights() == 0):
            self.log("Ignoring callback because lights are off", level = "DEBUG")
            return

        if(self.count_on_media_players() > 0):
            self.log("Ignoring callback because media_players are still on", level = "DEBUG")
            return

        if(self.is_alarm_triggered() or self.is_alarm_pending()):
            self.log("Ignoring callback because alarm state is {}".format(self.get_alarm_state()), level = "DEBUG")
            return

        if self._off_scene is not None:
            self.log("Activating scene {}".format(self._off_scene))
            self.turn_on(self._off_scene)

    def motion_on_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback motion_on from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.below_min_illumination()):
            self.turn_on_lights()

    def motion_off_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback motion_off from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.count_on_motion_sensors > 0):
            self.log("Ignoring callback because there is still motion", level = "DEBUG")
            return

        self.turn_off_lights()

    def illumination_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback illumination_change from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.below_min_illumination(new)):
            if(self.below_min_illumination(old)):
                self.log("Ignoring callback because old value was already below illumination threshold", level = "DEBUG")
                return
            self.turn_on_lights()
        elif(self.above_max_illumination(new)):
            if(self.above_max_illumination(old)):
                self.log("Ignoring callback because old value was already above illumination threshold", level = "DEBUG")
                return
            self.turn_off_lights()

    def elevation_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback elevation_change from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.below_min_elevation(old)):
            self.log("Ignoring callback because old value was already below min elevation", level = "DEBUG")
            return

        if(self.above_max_illumination()):
            self.log("Ignoring callback because illumation above threshold", level = "DEBUG")
            return

        if(self.below_min_elevation()):
            self.turn_on_lights()

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

        self.turn_off_power()



    def update_fluxer(self, kwargs):
        if self._fluxer_switch == None:
            return

        if(self.is_alarm_triggered() or self.is_alarm_pending()):
            self.log("Ignoring update because alarm state is {}".format(self.get_alarm_state()), level = "DEBUG")
            self._fluxer_handle = self.run_in(self.update_fluxer, self._fluxer_interval)
            return

        # FIXME does not seem to work
        if(self.now_is_between(self._night_start, self._night_end)):
            self.log("Ignoring update because in night mode")
            self._fluxer_handle = self.run_in(self.update_fluxer, self._fluxer_interval)
            return

        self.log("Updating fluxer {}".format(self._fluxer_switch))
        self.call_service("{}_update".format(self._fluxer_switch.replace('.', '/')))

        self._fluxer_handle = self.run_in(self.update_fluxer, self._fluxer_interval)

    def start_fluxer(self):
        if self._fluxer_switch == None:
            return

        self.stop_fluxer()
        self.log("Starting fluxer timer".format())
        self._fluxer_handle = self.run_in(self.update_fluxer, 1)

    def stop_fluxer(self):
        if self._fluxer_switch == None:
            return

        if self._fluxer_handle is not None:
            self.log("Stopping fluxer timer")
            self.cancel_timer(self._fluxer_handle)
            self._fluxer_handle = None

    def is_fluxer_running(self):
        return self._fluxer_handle is not None
