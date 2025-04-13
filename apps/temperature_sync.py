import appdaemon.plugins.hass.hassapi as hass
import datetime
import time
import re
import inspect

#
# TemperatureSync App
#
# Args:
#


class TemperatureSync(hass.Hass):

    def initialize(self):
        self.log("Hello from TemperatureSync")

        self._input = self.args.get("input")
        self._outputs = self.args.get("outputs", [])

        self.listen_state(self.sensor_change_callback, self._input)

        # Set start time to now, aligning to the next full 10-minute mark
        self.run_every(self.perodic_time_callback, "now+10", 10 * 60)

    def perodic_time_callback(self, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name}")

        self.sync_temperature()

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        self.sync_temperature()

    def sync_temperature(self):
        temperature = self.get_state(self._input)
        for entity_id in self._outputs:
            self.log(f"[{entity_id}] Setting number value to {temperature}")
            self.call_service("number/set_value", entity_id=entity_id, value=temperature)
