"""AwtrixControl app: send notifications and power commands to AWTRIX devices via MQTT.

Main features:
- Publish power/sleep/notification payloads to configured AWTRIX MQTT prefixes.
- React to motion, device tracker and alarm events to power on/off or display messages.

Key configuration keys:
- awtrix_prefixes: list of MQTT topic prefixes for your AWTRIX devices (required).

Example:
```yaml
awtrix:
    module: awtrix
    class: AwtrixControl
    awtrix_prefixes:
        - "awtrix/device1"
        - "awtrix/device2"
```

See module docstring and inline examples for usage.
"""

from base import BaseApp
import json
import inspect



class AwtrixControl(BaseApp):

    def initialize(self):
        """Set up AwtrixControl: read args, register listeners and start periodic timer.

        Side effects:
            - Registers state listeners for device trackers, motion sensors and alarm panel.
            - Starts a periodic timer for periodic tasks.
        """
        super().initialize()

        # awtrix devices
        self.__awtrix_prefixes = self.args.get("awtrix_prefixes", [])

        # stop power if nobody is home
        for sensor in self._device_trackers:
            self.listen_state(self.sensor_change_callback,
                                sensor, new="home", old="not_home", duration=self._tracker_timeout)

        # start or stop power based on motion
        for sensor in self._motion_sensors:
            self.listen_state(self.sensor_change_callback, sensor,
                                new="on", old="off")
            self.listen_state(self.sensor_change_callback, sensor,
                                new="off", old="on", duration=self._motion_timeout)

        # start in alarm state
        if self._alarm_control_panel is not None:
            self.listen_state(self.sensor_change_callback, self._alarm_control_panel, new="triggered")
            self.listen_state(self.sensor_change_callback, self._alarm_control_panel, new="pending")

        # Set start time to now, aligning to the next full 10-minute mark
        self.run_every(self.periodic_time_callback, "now+15", 10 * 60)

        self.log("Startup finished")


    def setup(self):
        """Evaluate current conditions and decide whether to turn AWTRIX on/off.

        This method is invoked on startup and from event callbacks. It checks
        motion, alarm and night windows and triggers `turn_on`/`sleep` as needed.
        """
        # get_last_motion() may return None when no motion data is available;
        # avoid formatting None with numeric format specifiers which raises
        # TypeError. Use a safe representation instead.
        last_motion = self.get_last_motion()
        if last_motion is None:
            self.log("Last motion occurred: unknown (no data)")
        else:
            self.log(f"Last motion occurred {last_motion:.2f} seconds ago")

        if(self.count_on_motion_sensors() > 0):
            self.log(f"Turning on awtrix because motion was detected on {self.count_on_motion_sensors()} sensors")
            self.turn_on()
            return
        if(self.is_alarm_triggered() or self.is_alarm_pending()):
            self.log("Turning on awtrix because alarm is triggered or pending")
            self.turn_on()
            return
        if(self.is_time_in_night_window()):
            self.log(f"Sleeping {self.get_seconds_until_night_end()} seconds until night time ends")
            self.sleep(self.get_seconds_until_night_end())
            return
        if(self.count_on_motion_sensors() == 0):
            self.log("Sleeping 60 seconds until next motion")
            self.sleep(60)
            #self.turn_off()
            return

    def periodic_time_callback(self, kwargs):
        """Periodic callback invoked by run_every; re-evaluates setup.

        Args:
            kwargs (dict): AppDaemon passes timer kwargs here (ignored).
        """
        self.log(f"{inspect.currentframe().f_code.co_name}")
        self.setup()

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        """Generic sensor change handler that triggers a re-check.

        Args:
            entity (str): entity id that changed.
            attribute (str): attribute that changed.
            old (str): previous state value.
            new (str): new state value.
            kwargs (dict): additional AppDaemon kwargs.
        """
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")
        self.setup()

    def send_mqtt(self, prefix, payload):
        """Publish a JSON payload to each configured AWTRIX MQTT prefix.

        Args:
            prefix (str): topic suffix to publish (e.g., 'power', 'sleep').
            payload (dict): data to JSON-encode and publish.
        """
        for device_prefix in self.__awtrix_prefixes:
            # Convert the dictionary to a JSON string
            payload_json = json.dumps(payload)
            topic = device_prefix + "/" + prefix

            self.log(f"Calling service mqtt/publish with topic {topic} and payload: {payload_json}")
            self.call_service('mqtt/publish',
                                topic=topic,
                                payload=payload_json)

    def turn_on(self):
        """Turn AWTRIX devices on via MQTT payload."""
        payload = {
            "power": True
        }
        self.send_mqtt('power', payload)

    def turn_off(self):
        """Turn AWTRIX devices off via MQTT payload."""
        payload = {
            "power": False
        }
        self.send_mqtt('power', payload)

    def sleep(self, seconds = 60):
        """Put AWTRIX devices to sleep for the specified number of seconds.

        Args:
            seconds (int): sleep duration in seconds.
        """
        payload = {
            "sleep": seconds
        }
        self.send_mqtt('sleep', payload)