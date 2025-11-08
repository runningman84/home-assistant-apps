"""TemperatureSync app: synchronize a source temperature sensor to multiple target entities.

Main features:
- Mirror a numeric temperature sensor to one or more `number` entities or setpoint controls.
- Validate numeric input and ignore invalid sensor states.

Key configuration keys:
- input: entity id of the source temperature sensor (required).
- outputs: list of target entity ids to set (e.g., number.setpoint_*).

Example:
```yaml
temperature_sync:
    module: temperature_sync
    class: TemperatureSync
    input: sensor.temperature_outside
    outputs:
        - number.setpoint_living
        - number.setpoint_bedroom
```

See module docstring and inline examples for usage.
"""

import appdaemon.plugins.hass.hassapi as hass
import datetime
import time
import re
import inspect



class TemperatureSync(hass.Hass):

    def initialize(self):
        self.log("Hello from TemperatureSync")

        self._input = self.args.get("input")
        self._outputs = self.args.get("outputs", [])

        self.listen_state(self.sensor_change_callback, self._input)

        # Set start time to now, aligning to the next full 10-minute mark
        self.run_every(self.periodic_time_callback, "now+10", 10 * 60)

    def periodic_time_callback(self, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name}")

        self.sync_temperature()

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        self.sync_temperature()

    def sync_temperature(self):
        temperature = self.get_state(self._input)

        try:
            numeric_value = float(temperature)
            # Proceed with numeric_value
        except (TypeError, ValueError):
            self.error(f"Ignoring invalid temperature value: {temperature}")
            return

        for entity_id in self._outputs:
            self.log(f"[{entity_id}] Setting number value to {temperature}")
            self.call_service("number/set_value", entity_id=entity_id, value=temperature)
