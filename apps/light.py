import appdaemon.plugins.hass.hassapi as hass
from base import BaseApp
from datetime import datetime, timezone
import inspect

#
# LightControl App
#
# Args:
#
# Concept:
# PowerOn if motion
# PowerOff if no motion for motion_timeout
# PowerOff if vacation for vacation_duration
# PowerOff if nobody at home for tracker_timeout unless guest
# Nothing on startup

class LightControl(BaseApp):

    def initialize(self):
        super().initialize()

        # setup sane defaults
        self._lights = self.args.get("lights", [])
        self._fluxer_switch = self.args.get("fluxer_switch", None)
        # self._fluxer_interval = self.args.get("fluxer_interval", 300)
        # self._fluxer_handle = None

        self._min_elevation = self.args.get("min_elevation", 10)
        self._min_illumination = self.args.get("min_illumination", 25)
        self._max_illumination = self.args.get("max_illumination", 150)

        self._night_scene = self.args.get("night_scene", None)
        self._on_scene = self.args.get("on_scene", None)
        self._off_scene = self.args.get("off_scene", None)
        self._auto_turn_off = self.args.get("auto_turn_off", True)
        self._auto_turn_on = self.args.get("auto_turn_on", True)

        # log current config
        self.log("Got lights {}".format(self._lights))

        # start or stop power based on motion
        for sensor in self._motion_sensors:
            self.listen_state(self.sensor_change_callback, sensor,
                                new="on", old="off")
            self.listen_state(self.sensor_change_callback, sensor,
                                new="off", old="on", duration=self._motion_timeout)

        # change based on light control
        for light_control in self._lights:
            # record changes
            self.listen_state(self.control_change_callback, light_control, new="on", old="off")
            self.listen_state(self.control_change_callback, light_control, new="off", old="on")
            # act on changes delayed
            self.listen_state(self.sensor_change_callback, light_control, new="on", old="off", duration=60)
            self.listen_state(self.sensor_change_callback, light_control, new="off", old="on", duration=60)

        if self._fluxer_switch is not None:
            # record changes
            self.listen_state(self.control_change_callback, self._fluxer_switch, new="on", old="off")
            self.listen_state(self.control_change_callback, self._fluxer_switch, new="off", old="on")

        # start or stop based on media player stuff
        for sensor in self._media_players:
            self.listen_state(self.sensor_change_callback, sensor,
                                new="on", old="off")

        # stop power if nobody is home
        for sensor in self._device_trackers:
            self.listen_state(self.sensor_change_callback,
                                sensor, new="not_home", old="home", duration=self._tracker_timeout)

        # stop power during vacation
        if self._vacation_control is not None:
            self.listen_state(self.sensor_change_callback, self._vacation_control,
                                new="on", old="off", duration=self._vacation_timeout)

        # start power based on illumination
        for sensor in self._illumination_sensors:
            self.listen_state(self.sensor_change_callback, sensor)

        # start or stop power based on elevation
        self.listen_state(self.sensor_change_callback, "sun.sun", attribute = "elevation")

        if self._alarm_control_panel is not None and self._fluxer_switch is not None:
            self.listen_state(self.flux_change_callback, self._alarm_control_panel)

        # Set start time to now, aligning to the next full 10-minute mark
        self.run_every(self.perodic_time_callback, "now+10", 10 * 60)

        self.log("Startup finished")


    def below_min_elevation(self):
        if self.get_state("sun.sun", attribute = "elevation") < self._min_elevation:
            return True
        return False

    def below_min_illumination(self):
        for sensor in self._illumination_sensors:
            if self.get_state(sensor) == None:
                return True
            if self.get_state(sensor) == 'unknown':
                return True
            if self.get_state(sensor) == 'unavailable':
                return True
            if float(self.get_state(sensor)) < self._min_illumination:
                return True
        return False

    def above_max_illumination(self):
        for sensor in self._illumination_sensors:
            if self.get_state(sensor) == None:
                return False
            if self.get_state(sensor) == 'unknown':
                return False
            if self.get_state(sensor) == 'unavailable':
                return False
            if float(self.get_state(sensor)) > self._max_illumination:
                return True
        return False

    def perodic_time_callback(self, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name}")

        self.update_lights()

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        self.update_lights()

    def update_lights(self):
        last_change = self.get_last_motion()

        if(self.is_internal_change_allowed() == False):
            remaining_seconds = self.get_remaining_seconds_before_internal_change_is_allowed()
            self.log(f"Doing nothing: Internal change is not allowed for {remaining_seconds} more seconds.")
            return

        if(self.is_nobody_at_home()):
            self.log("Turning off lights because nobody is at home")
            self.turn_off_lights()
            return

        if(self.in_vacation_mode()):
            self.log("Turning off lights because of vacation")
            self.turn_off_lights()
            return

        if(self.count_on_motion_sensors() == 0 and self.count_motion_sensors('any') > 0):
            self.log(f"Turning off lights because of last motion was {last_change:.2f} seconds ago")
            self.turn_off_lights()
            return

        if(self.is_alarm_armed_away()):
            self.log("Turning off lights because of alarm is armed away")
            self.turn_off_lights()
            return

        if(self.is_alarm_armed_vacation()):
            self.log("Turning off lights because of alarm is armed vacation")
            self.turn_off_lights()
            return

        if(self.is_alarm_triggered() or self.is_alarm_pending()):
            self.log("Doing nothing because alarm is triggered or pending")
            return

        #if(self.count_motion_sensors('any') > 0):
        #    self.log(f"Might turning on lights because of last motion was {last_change} seconds ago")

        if(self._min_illumination is not None and self.below_min_illumination()):
            self.log("Turning on lights because below min illumination")
            self.turn_on_lights()
            return
        elif(self._min_elevation is not None and self.below_min_elevation()):
            self.log("Turning on lights because below min elevation")
            self.turn_on_lights()
            return
        elif(self._max_illumination is not None and self.above_max_illumination()):
            self.log("Turning off lights because above max illumination")
            self.turn_off_lights()
            return

    def turn_on_lights(self):
        if self.count_lights("any") == self.count_lights("on"):
            self.log("All lights are already on")
            return

        if self.is_auto_turn_on_disabled():
            self.log("Automatic turn on is disabled")
            return

        if self.is_time_in_night_window():
            if self._night_scene is not None:
                self.log(f"Activating night scene {self._night_scene}")
                #self.stop_fluxer()
                self.turn_on(self._night_scene)
        else:
            if self._on_scene is not None:
                self.log(f"Activating normal scene {self._on_scene}")
                #self.start_fluxer()
                self.turn_on(self._on_scene)
            else:
                for light_control in self._lights:
                    self.log(f"Turning on light {light_control}")
                    self.turn_on(light_control)

        self.record_internal_change()

    def turn_off_lights(self):
        if self.count_lights("any") == self.count_lights("off"):
            self.log("All lights are already off")
            return

        if self.is_auto_turn_off_disabled():
            self.log("Automatic turn off is disabled")
            return

        if self._off_scene is not None:
            self.log(f"Activating normal scene {self._off_scene}")
            self.turn_on(self._off_scene)
        else:
            for light_control in self._lights:
                self.log(f"Turning off light {light_control}")
                self.turn_off(light_control)

        self.record_internal_change()

    def is_auto_turn_on_enabled(self):
        return self._auto_turn_on

    def is_auto_turn_off_enabled(self):
        return self._auto_turn_off

    def is_auto_turn_on_disabled(self):
        return not self.is_auto_turn_on_enabled()

    def is_auto_turn_off_disabled(self):
        return not self.is_auto_turn_off_enabled()

    def flux_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        if self._fluxer_switch is None:
            return

        if new in ['pending', 'triggered', 'arming', 'armed_away', 'armed_vacation', 'armed_night']:
            if self.get_state(self._fluxer_switch) == 'on':
                self.log(f"Turning off {self._fluxer_switch} because alarm state changed from {old} to {new}")
                self.turn_off(self._fluxer_switch)
                self.record_internal_change()
            else:
                self.log(f"Flux {self._fluxer_switch} is already on")
        if new in ['disarmed', 'armed_home']:
            if self.get_state(self._fluxer_switch) == 'off':
                self.log(f"Turning on {self._fluxer_switch} because alarm state changed from {old} to {new}")
                self.turn_on(self._fluxer_switch)
                self.record_internal_change()
            else:
                self.log(f"Flux {self._fluxer_switch} is already off")
