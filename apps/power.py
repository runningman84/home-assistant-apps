"""PowerControl app: manage power outlets and devices based on motion, presence and schedules.

Main features:
- Automatically switch power controls on/off based on motion, presence, media playback and schedules.
- Respect vacation and alarm states to avoid turning devices on when not desired.
- Track and count switches and provide simple group operations.

Key configuration keys:
- power_controls: list of switch entity ids to control (required).
- motion_sensors, device_trackers: optional lists to decide when to turn devices on/off.
- tracker_duration: how long after last device_tracker presence to consider someone present.
- night_start: time to perform nightly power actions (configure via BaseApp defaults).

Example:
```yaml
power_control:
    module: power
    class: PowerControl
    power_controls:
        - switch.tv_living_room
        - switch.receiver
    motion_sensors:
        - binary_sensor.motion_living
    tracker_duration: 60
```

See module docstring and inline examples for usage.
"""

import appdaemon.plugins.hass.hassapi as hass
from base import BaseApp
import inspect



class PowerControl(BaseApp):

    def initialize(self):
        super().initialize()

        # setup sane defaults
        self._power_controls = self.args.get("power_controls", [])
        self._standby_sensors = self.args.get("standby_sensors", [])
        self._standby_threshold = None
        self._night_force_off = self.args.get("night_force_off", True)

        # TBD
        self._standby_power_limit = self.args.get("standby_power_limit", 0)
        self._standby_power_limit_last_seen = self.args.get("standby_power_limit", None)

        # log current config
        self.log(f"Got device controls {self._power_controls}")

        # start or stop power based on motion
        for sensor in self._motion_sensors:
            self.listen_state(self.sensor_change_callback, sensor,
                                new="on", old="off")
            self.listen_state(self.sensor_change_callback,
                                sensor, new="off", old="on", duration=self._motion_timeout)

        # stop power if nobody is home
        for sensor in self._device_trackers:
            self.listen_state(self.sensor_change_callback,
                                sensor, new="not_home", old="home", duration=self._tracker_timeout)

        # stop power during vacation
        if self._vacation_control is not None:
            self.listen_state(self.sensor_change_callback, self._vacation_control,
                                new="on", old="off", duration=self._vacation_timeout)

        # stop power each night
        runtime = self.parse_time(self._night_start)
        self.run_daily(self.periodic_time_callback, runtime)

        # change based on power control
        for power_control in self._power_controls:
            # record changes
            self.listen_state(self.control_change_callback, power_control, new="on", old="off")
            self.listen_state(self.control_change_callback, power_control, new="off", old="on")
            # act on changes delayed
            self.listen_state(self.sensor_change_callback, power_control, new="on", old="off", duration=60)
            self.listen_state(self.sensor_change_callback, power_control, new="off", old="on", duration=60)


        # Set start time to now, aligning to the next full 10-minute mark
        self.run_every(self.periodic_time_callback, "now+10", 10 * 60)

        self.log("Startup finished")

    def count_switches(self, state = None):
        self.log(f"count switches in state {state}", level = "DEBUG")
        if state is None:
            return len(self._power_controls)

        count = 0
        for sensor in self._power_controls:
            self.log(f"switch {sensor} is in state {self.get_state(sensor)}", level = "DEBUG")
            if self.get_state(sensor) == state:
                count = count + 1

        self.log(f"found {count} switch in state {state}", level = "DEBUG")
        return count

    def count_on_switches(self):
        return self.count_switches("on")

    def count_off_switches(self):
        return self.count_switches("off")

    def update_power(self):
        if(self.is_internal_change_allowed() == False):
            remaining_seconds = self.get_remaining_seconds_before_internal_change_is_allowed()
            self.log(f"Doing nothing: Internal change is not allowed for {remaining_seconds:.2f} more seconds.")
            return

        if(self.is_nobody_at_home()):
            self.log("Turning off power because nobody is at home")
            self.turn_off_power()
            return

        if(self.in_vacation_mode()):
            self.log("Turning off power because of vacation")
            self.turn_off_power()
            return

        if(self.count_media_players('playing', ['Spotify', 'JUKE', 'Qobuz', 'AirPlay', 'MC Link', 'Server', 'Net Radio', 'Bluetooth', 'USB', 'Tuner'])):
            self.log("Doing nothing because media player is playing music")
            return

        if(self.count_on_motion_sensors() == 0 and self.count_motion_sensors() > 0):
            self.log(f"Turning off power because of last motion was {self.get_last_motion():.2f} seconds ago")
            self.turn_off_power()
            return

        if(self.is_alarm_armed_away()):
            self.log("Turning off power because of alarm is armed away")
            self.turn_off_power()
            return

        if(self.is_alarm_armed_vacation()):
            self.log("Turning off power because of alarm is armed vacation")
            self.turn_off_power()
            return

        if(self.is_alarm_triggered() or self.is_alarm_pending()):
            self.log("Doing nothing because alarm is triggered or pending")
            return

        self.log(f"Turning on power because of last motion was {self.get_last_motion():.2f} seconds ago")
        self.turn_on_power()

    def turn_on_power(self):
        if self.count_switches() == self.count_switches("on"):
            self.log("All switches are already on")
            return

        for device_control in self._power_controls:
            self.log(f"Turning on switch {device_control}")
            self.turn_on(device_control)

        self.record_internal_change()

    def turn_off_power(self):
        if self.count_switches() == self.count_switches("off"):
            self.log("All switches are already off")
            return

        for device_control in self._power_controls:
            self.log(f"Turning off switch {device_control}")
            self.turn_off(device_control)

        self.record_internal_change()

    def periodic_time_callback(self, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name}")

        self.update_power()

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        self.update_power()
