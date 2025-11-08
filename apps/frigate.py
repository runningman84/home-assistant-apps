"""FrigateControl app: coordinate Frigate camera service with Home Assistant states and triggers.

Main features:
- Turn on/off Frigate camera recording/switches based on motion, openings, alarm and schedule.
- Provide grouped operations for cameras and switches and options to auto-enable/disable on certain events.

Key configuration keys:
- frigate_switches: list of switch entity ids to enable/disable Frigate recording or related integrations.
- frigate_cameras: list of camera entity ids to monitor/control.
- auto_turn_on_motion/opening/alarm: booleans to enable auto-start for corresponding events.

See module docstring and inline examples for usage.
"""

from base import BaseApp
import inspect



class FrigateControl(BaseApp):

    def initialize(self):
        """
        Initialize FrigateControl: read args, register listeners and schedule periodic checks.

        This wires frigate switches, cameras and various sensors to callbacks so
        `setup()` can react to state changes and timers.
        """
        super().initialize()

        self._frigate_switches = self.args.get("frigate_switches", [])
        self._frigate_cameras = self.args.get("frigate_cameras", [])

        self._auto_turn_on_motion = self.args.get("auto_turn_on_motion", True)
        self._auto_turn_on_opening = self.args.get("auto_turn_on_opening", True)
        self._auto_turn_on_alarm = self.args.get("auto_turn_on_alarm", True)

        self._auto_turn_off_motion = self.args.get("auto_turn_off_motion", True)
        self._auto_turn_off_opening = self.args.get("auto_turn_off_opening", True)
        self._auto_turn_off_alarm = self.args.get("auto_turn_off_alarm", True)

        self.log(f"Got frigate cameras: {self._frigate_cameras}")
        self.log(f"Got frigate switches: {self._frigate_switches}")

        # change based on frigate switches
        for switch in self._frigate_switches:
            # record changes
            self.listen_state(self.control_change_callback, switch, new="on", old="off")
            self.listen_state(self.control_change_callback, switch, new="off", old="on")

        # change based on frigate cameras
        for camera in self._frigate_cameras:
            # record changes
            self.listen_state(self.control_change_callback, camera, new="streaming", old="idle")
            self.listen_state(self.control_change_callback, camera, new="idle", old="streaming")

        # listen for alarm state changes
        if self._alarm_control_panel is not None:
            self.listen_state(self.sensor_change_callback, self._alarm_control_panel)

        # listen for window and door openings
        for sensor in self._opening_sensors:
            self.listen_state(self.sensor_change_callback, sensor,
                                new="on", old="off")
            self.listen_state(self.sensor_change_callback, sensor,
                                new="off", old="on", duration=self._opening_timeout)

        # listen for motion changes
        for sensor in self._motion_sensors:
            self.listen_state(self.sensor_change_callback, sensor,
                                new="on", old="off")
            self.listen_state(self.sensor_change_callback, sensor,
                                new="off", old="on", duration=self._motion_timeout)

        # Set start time to now, aligning to the next full 10-minute mark
        self.run_every(self.periodic_time_callback, "now+15", 10 * 60)

        self.log("Startup finished")


    def setup(self):
        """
        Evaluate configured sensors and decide whether to (de)activate Frigate.

        This central method is invoked from timers and state-change callbacks
        and will call the appropriate turn_on/turn_off helpers based on the
        configured auto_turn_on/auto_turn_off flags and the internal change
        policy provided by `BaseApp`.
        """
        if not self.is_internal_change_allowed():
            remaining_seconds = self.get_remaining_seconds_before_internal_change_is_allowed()
            self.log(f"Doing nothing: Internal change is not allowed for {remaining_seconds} more seconds.")
            return

        if self._auto_turn_on_motion:
            if(self.count_motion_sensors("on") > 0 and self.count_motion_sensors() > 0):
                self.log("Turning on frigate because there is motion")
                self.turn_on_frigate()
                return

        if self._auto_turn_on_opening:
            if(self.count_opening_sensors("on") > 0 and self.count_opening_sensors() > 0):
                self.log("Turning on frigate because doors or windows are open")
                self.turn_on_frigate()
                return

        if self._auto_turn_on_alarm:
            if(self.is_alarm_triggered() or self.is_alarm_arming() or self.is_alarm_pending() or self.is_alarm_armed()):
                self.log("Turning on frigate because alarm is triggered, arming, pending or armed")
                self.turn_on_frigate()
                return

        if self._auto_turn_off_motion:
            if(self.count_motion_sensors("off") == self.count_motion_sensors() and self.count_motion_sensors() > 0):
                self.log("Turning off frigate because there is no motion")
                self.turn_off_frigate()
                return

        if self._auto_turn_off_opening:
            if(self.count_opening_sensors("off") == self.count_opening_sensors() and self.count_opening_sensors() > 0):
                self.log("Turning off frigate because doors or windows are closed")
                self.turn_off_frigate()
                return

        if self._auto_turn_off_alarm:
            if(self.is_alarm_disarmed()):
                self.log("Turning off frigate because alarm is disarmed")
                self.turn_off_frigate()
                return

    def periodic_time_callback(self, kwargs):
        """
        Periodic timer callback scheduled via run_every/run_daily.

        Args:
            kwargs (dict): timer arguments passed by AppDaemon (ignored).
        """

        self.log(f"{inspect.currentframe().f_code.co_name}")

        self.setup()

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        """
        Generic state-change handler that triggers a re-evaluation of Frigate state.

        Args:
            entity (str): entity id that changed.
            attribute (str): attribute that changed.
            old (str): previous state value.
            new (str): new state value.
            kwargs (dict): AppDaemon-provided kwargs.
        """

        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        self.setup()

    def count_switches(self, state = None):
        """Return number of configured switches optionally filtered by state.

        Args:
            state: Optional string state to filter by (e.g. 'on' or 'off').

        Returns:
            int: count of switches matching the state or total switches when
            state is None.
        """

        self.log(f"Count switches in state {state}", level = "DEBUG")
        if state is None:
            return len(self._frigate_switches)

        count = 0
        for sensor in self._frigate_switches:
            self.log(f"Switch {sensor} is in state {self.get_state(sensor)}", level = "DEBUG")
            if self.get_state(sensor) == state:
                count = count + 1

        self.log(f"Found {count} switches in state {state}", level = "DEBUG")
        return count

    def count_on_switches(self):
        """Shortcut: count switches in 'on' state."""

        return self.count_switches("on")

    def count_off_switches(self):
        """Shortcut: count switches in 'off' state."""

        return self.count_switches("off")

    def count_any_switches(self):
        """Shortcut: count all configured switches."""

        return self.count_switches()

    def count_cameras(self, state = None):
        """Return number of configured cameras optionally filtered by state.

        Args:
            state: Optional string state to filter by (e.g. 'streaming' or 'idle').

        Returns:
            int: count of cameras matching the state or total cameras when
            state is None.
        """

        self.log(f"Count cameras in state {state}", level = "DEBUG")
        if state is None:
            return len(self._frigate_cameras)

        count = 0
        for sensor in self._frigate_cameras:
            self.log(f"Camera {sensor} is in state {self.get_state(sensor)}", level = "DEBUG")
            if self.get_state(sensor) == state:
                count = count + 1

        self.log(f"Found {count} cameras in state {state}", level = "DEBUG")
        return count

    def count_streaming_cameras(self):
        """Shortcut: count cameras currently streaming."""

        return self.count_cameras("streaming")

    def count_idle_cameras(self):
        """Shortcut: count cameras currently idle."""

        return self.count_cameras("idle")

    def count_any_cameras(self):
        """Shortcut: count all configured cameras."""

        return self.count_cameras()

    def turn_on_frigate(self):
        """Enable all configured Frigate cameras and switches.

        This triggers both camera service calls and switch turn_on calls and
        records the internal change so other listeners can ignore the
        resulting state-changes for a short period.
        """

        self.turn_on_frigate_cameras()
        self.turn_on_frigate_switches()

    def turn_off_frigate(self):
        """Disable all configured Frigate cameras and switches and record change."""

        self.turn_off_frigate_cameras()
        self.turn_off_frigate_switches()

    def turn_on_frigate_switches(self):
        """Turn on configured Frigate switches unless already all on."""

        if self.count_on_switches() == self.count_any_switches():
            self.log("All switches are already on")
            return

        for switch in self._frigate_switches:
            self.log(f"Turning on switch {switch}")
            self.turn_on(switch)

        self.record_internal_change()

    def turn_off_frigate_switches(self):
        """Turn off configured Frigate switches unless already all off."""

        if self.count_off_switches() == self.count_any_switches():
            self.log("All switches are already off")
            return

        for switch in self._frigate_switches:
            self.log(f"Turning on switch {switch}")
            self.turn_off(switch)

        self.record_internal_change()

    def turn_on_frigate_cameras(self):
        """Call camera.turn_on for all configured cameras unless already streaming."""

        if self.count_streaming_cameras() == self.count_any_cameras():
            self.log("All cameras are already streaming")
            return

        for camera in self._frigate_cameras:
            self.log(f"Turning on camera {camera}")
            self.call_service("camera/turn_on", entity_id=camera)

        self.record_internal_change()

    def turn_off_frigate_cameras(self):
        """Call camera.turn_off for all configured cameras unless already idle."""

        if self.count_idle_cameras() == self.count_any_cameras():
            self.log("All cameras are already idle")
            return

        for camera in self._frigate_cameras:
            self.log(f"Turning off camera {camera}")
            self.call_service("camera/turn_off", entity_id=camera)

        self.record_internal_change()
