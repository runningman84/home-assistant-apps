from base import BaseApp
import json
import inspect

class AwtrixControl(BaseApp):

    def initialize(self):
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
        self.run_every(self.perodic_time_callback, "now+15", 10 * 60)

        self.log("Startup finished")


    def setup(self):
        self.log(f"Last motion occured {self.get_last_motion():.2f} seconds ago")

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
            self.log(f"Sleeping 60 seconds until next motion")
            self.sleep(60)
            #self.turn_off()
            return

    def perodic_time_callback(self, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name}")
        self.setup()

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")
        self.setup()

    def send_mqtt(self, prefix, payload):
        for device_prefix in self.__awtrix_prefixes:
            # Convert the dictionary to a JSON string
            payload_json = json.dumps(payload)
            topic = device_prefix + "/" + prefix

            self.log(f"Calling service mqtt/publish with topic {topic} and payload: {payload_json}")
            self.call_service('mqtt/publish',
                                topic=topic,
                                payload=payload_json)

    def turn_on(self):
        payload = {
            "power": True
        }
        self.send_mqtt('power', payload)

    def turn_off(self):
        payload = {
            "power": False
        }
        self.send_mqtt('power', payload)

    def sleep(self, seconds = 60):
        payload = {
            "sleep": seconds
        }
        self.send_mqtt('sleep', payload)