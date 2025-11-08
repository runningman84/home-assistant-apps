"""CameraImageScanner app: trigger and manage image processing scans for configured cameras.

Main features:
- Trigger image_processing scans when configured sensors (e.g., motion) change.
- Manage scan scheduling, throttling and automatic stop when inactivity is detected.

Key configuration keys:
- image_processor: entity_id of an image_processing configuration to call via service.
- sensors: list of binary_sensor ids that should trigger scans.

Example:
```yaml
camera_scanner:
    module: camera
    class: CameraImageScanner
    image_processor: image_processing.my_person_detector
    sensors:
        - binary_sensor.motion_front_door
```

See module docstring and inline examples for usage.
"""

import appdaemon.plugins.hass.hassapi as hass



class CameraImageScanner(hass.Hass):

    def initialize(self):
        self.log("Hello from CameraImageScanner")

        self._processing_handle = None
        self._processing_count = 0
        self._processing_max_count = 10000

        # setup sane defaults
        self._image_processor = self.args.get("image_processor", None)
        self._sensors = self.args.get("sensors", [])

        self._sensor_handles = {}

        for sensor in self._sensors:
            self.listen_state(self.trigger_start_image_scan_callback, sensor, new="on", old="off")
            self.listen_state(self.trigger_stop_image_scan_callback, sensor, new="off", old="on")

    def trigger_start_image_scan_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback trigger_image_scan_callback from {}:{} {}->{}".format(entity, attribute, old, new))
        self.start_image_processing()
    
    def trigger_stop_image_scan_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback trigger_stop_image_scan_callback from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.count_on_sensors() > 0):
            self.log("Ignoring status {} of {} because {} sensors are still in status on".format(
                new, entity, self.count_on_sensors()))
            return

        self.stop_image_processing()

    def count_sensors(self, state):
        count = 0
        for sensor in self._sensors:
            if self.get_state(sensor) == state:
                count = count + 1
        return count

    def count_on_sensors(self):
        return self.count_sensors("on")

    def count_off_sensors(self):
        return self.count_sensors("off")
    
    def get_next_run_in_sec(self):
        seconds = 1
        if(self._processing_count < 1000):
            seconds = 60
        if(self._processing_count < 500):
            seconds = 15
        if(self._processing_count < 200):
            seconds = 10
        if(self._processing_count < 100):
            seconds = 5
        if(self._processing_count < 60):
            seconds = 2
        return seconds

    def process_image(self, kwargs):
        self.call_service(
                "image_processing/scan", entity_id=self._image_processor)
        self._processing_count += 1
        self.log("Image processing count {}".format(self._processing_count))
        if self._processing_count < self._processing_max_count:
            self._processing_handle = self.run_in(self.process_image, self.get_next_run_in_sec())

    def start_image_processing(self):
        self.stop_image_processing()
        self._processing_count = 0
        self.log("Starting image processing")
        self._processing_handle = self.run_in(self.process_image, self.get_next_run_in_sec())

    def stop_image_processing(self):
        if self._processing_handle is not None:
            self.log("Stopping image processing")
            self.cancel_timer(self._processing_handle)
            self._processing_count = self._processing_max_count
            self._processing_handle = None