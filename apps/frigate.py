from base import BaseApp
import json
import inspect

class FrigateControl(BaseApp):

    def initialize(self):
        super().initialize()

        self._frigate_switches = self.args.get("frigate_switches", [])

        self._auto_turn_on_motion = self.args.get("auto_turn_on_motion", True)
        self._auto_turn_on_opening = self.args.get("auto_turn_on_opening", True)
        self._auto_turn_on_alarm = self.args.get("auto_turn_on_alarm", True)

        self._auto_turn_off_motion = self.args.get("auto_turn_off_motion", True)
        self._auto_turn_off_opening = self.args.get("auto_turn_off_opening", True)
        self._auto_turn_off_alarm = self.args.get("auto_turn_off_alarm", True)

        # change based on frigate switches
        for switch in self._frigate_switches:
            # record changes
            self.listen_state(self.control_change_callback, switch, new="on", old="off")
            self.listen_state(self.control_change_callback, switch, new="off", old="on")

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
        self.run_every(self.perodic_time_callback, "now+15", 10 * 60)

        self.log("Startup finished")


    def setup(self):
        if(self.is_internal_change_allowed() == False):
            remaining_seconds = self.get_remaining_seconds_before_internal_change_is_allowed()
            self.log(f"Doing nothing: Internal change is not allowed for {remaining_seconds} more seconds.")
            return

        if self._auto_turn_on_motion:
            if(self.count_motion_sensors("on") > 0 and self.count_motion_sensors("any") > 0):
                self.log("Turning on frigate because there is motion")
                self.turn_on_frigate()
                return

        if self._auto_turn_on_opening:
            if(self.count_opening_sensors("on") > 0 and self.count_opening_sensors("any") > 0):
                self.log("Turning on frigate because doors or windows are open")
                self.turn_on_frigate()
                return

        if self._auto_turn_on_alarm:
            if(self.is_alarm_triggered() or self.is_alarm_arming() or self.is_alarm_pending() or self.is_alarm_armed()):
                self.log("Turning on frigate because alarm is triggered, arming, pending or armed")
                self.turn_on_frigate()
                return

        if self._auto_turn_off_motion:
            if(self.count_motion_sensors("off") == self.count_motion_sensors("any") and self.count_motion_sensors("any") > 0):
                self.log("Turning off frigate because there is no motion")
                self.turn_off_frigate()
                return

        if self._auto_turn_off_opening:
            if(self.count_opening_sensors("off") == self.count_opening_sensors("any") and self.count_opening_sensors("any") > 0):
                self.log("Turning off frigate because doors or windows are closed")
                self.turn_off_frigate()
                return

        if self._auto_turn_off_alarm:
            if(self.is_alarm_disarmed()):
                self.log("Turning off frigate because alarm is disarmed")
                self.turn_off_frigate()
                return

    def perodic_time_callback(self, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name}")

        self.setup()

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        self.setup()

    def count_switches(self, state):
        self.log(f"Count switches in state {state}", level = "DEBUG")
        if state == 'any':
            return len(self._frigate_switches)

        count = 0
        for sensor in self._frigate_switches:
            self.log(f"Switch {sensor} is in state {self.get_state(sensor)}", level = "DEBUG")
            if self.get_state(sensor) == state:
                count = count + 1

        self.log(f"Found {count} switches in state {state}", level = "DEBUG")
        return count

    def count_on_switches(self):
        return self.count_switches("on")

    def count_off_switches(self):
        return self.count_switches("off")

    def count_any_switches(self):
        return self.count_switches("any")

    def turn_on_frigate(self):
        if self.count_on_switches() == self.count_any_switches():
            self.log("All switches are already on")
            return

        for switch in self._frigate_switches:
            self.log(f"Turning on switch {switch}")
            self.turn_on(switch)

        self.record_internal_change()

    def turn_off_frigate(self):
        if self.count_off_switches() == self.count_any_switches():
            self.log("All switches are already off")
            return

        for switch in self._frigate_switches:
            self.log(f"Turning on switch {switch}")
            self.turn_off(switch)

        self.record_internal_change()
