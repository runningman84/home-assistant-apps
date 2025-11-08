"""GuardDog app: simple guard logic that reacts to motion and door sensors and triggers alarms/ringtones.

Main features:
- Watch a motion sensor and a door sensor and trigger a ringtone when motion is detected while alarm is armed.

Key configuration keys:
- motion_sensor: entity_id of motion sensor (required).
- door_sensor: entity_id of a door sensor (required).
- gw_mac: gateway MAC for Xiaomi Aqara ringtone service (required for the example service call).

See module docstring and inline examples for usage.
"""

import appdaemon.plugins.hass.hassapi as hass



class GuardDog(hass.Hass):

    def initialize(self):
        self.log("Hello from GuardDog")

        self._motion_sensor = self.args["motion_sensor"]
        self._door_sensor = self.args["door_sensor"]
        self._gw_mac = self.args["gw_mac"]

        self.log("Guarding motion sensor {} at door sensor {}".format(self._motion_sensor, self._door_sensor))

        self.handle = self.listen_state(self.my_callback, self._motion_sensor)

    def my_callback(self, entity, attribute, old, new, kwargs):
        self.log("Callback from GuardDog")

        if self.get_state("alarm_control_panel.ha_alarm") == 'armed_home' or self.get_state("alarm_control_panel.ha_alarm") == 'armed_away':
            if self.get_state(self._door_sensor) == 'off' and new == 'on':
                self.call_service("xiaomi_aqara/play_ringtone", ringtone_id = 8, ringtone_vol = 20, gw_mac = self._gw_mac )
