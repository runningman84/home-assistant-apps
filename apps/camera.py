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
        """Initialize scanner: read args and register motion sensor listeners.

        Side effects:
            - Registers listeners on sensors to start/stop image scanning.
            - Starts a periodic run_every timer to manage processing cadence.
        """
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
        """Callback invoked when a sensor transitions to 'on' to start processing.

        Args:
            entity (str): entity id that changed.
            attribute (str): attribute that changed.
            old (str): previous state.
            new (str): new state.
            kwargs (dict): additional AppDaemon kwargs.
        """
        self.log(
            "Callback trigger_image_scan_callback from {}:{} {}->{}".format(entity, attribute, old, new))
        self.start_image_processing()
    
    def trigger_stop_image_scan_callback(self, entity, attribute, old, new, kwargs):
        """Callback invoked when a sensor transitions to 'off' to possibly stop processing.

        The method checks whether other sensors are still 'on' and only stops
        if none remain active.
        """
        self.log(
            "Callback trigger_stop_image_scan_callback from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.count_on_sensors() > 0):
            self.log("Ignoring status {} of {} because {} sensors are still in status on".format(
                new, entity, self.count_on_sensors()))
            return

        self.stop_image_processing()

    def count_sensors(self, state):
        """Count sensors in the configured `_sensors` list that match `state`.

        Args:
            state (str): state to compare (e.g., 'on' or 'off').

        Returns:
            int: number of matching sensors.
        """
        count = 0
        for sensor in self._sensors:
            if self.get_state(sensor) == state:
                count = count + 1
        return count

    def count_on_sensors(self):
        """Return count of configured sensors currently in state 'on'."""
        return self.count_sensors("on")

    def count_off_sensors(self):
        """Return count of configured sensors currently in state 'off'."""
        return self.count_sensors("off")
    
    def get_next_run_in_sec(self):
        """Return a dynamic retry interval (seconds) based on processing count.

        The implementation uses step thresholds to gradually shorten the interval
        when the processing count is low, allowing faster re-checks.
        """
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
        """Invoke the image_processing scan service for the configured processor.

        This method increments an internal counter and reschedules itself
        according to `get_next_run_in_sec` until the configured max count is reached.
        """
        self.call_service(
            "image_processing/scan", entity_id=self._image_processor)
        self._processing_count += 1
        self.log("Image processing count {}".format(self._processing_count))
        if self._processing_count < self._processing_max_count:
            self._processing_handle = self.run_in(self.process_image, self.get_next_run_in_sec())

    def start_image_processing(self):
        """Start a periodic image processing run sequence.

        Stops any existing handle, resets counters and schedules the first run.
        """
        self.stop_image_processing()
        self._processing_count = 0
        self.log("Starting image processing")
        self._processing_handle = self.run_in(self.process_image, self.get_next_run_in_sec())

    def stop_image_processing(self):
        """Stop any active image processing timer and mark processing as finished."""
        if self._processing_handle is not None:
            self.log("Stopping image processing")
            self.cancel_timer(self._processing_handle)
            self._processing_count = self._processing_max_count
            self._processing_handle = None