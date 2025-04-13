import appdaemon.plugins.hass.hassapi as hass

#
# Cleanup App
#
# Args:
#


class Cleanup(hass.Hass):

    def initialize(self):
        self.log("Hello from Cleanaup")

        self._processing_handle = None
        self._limit_number_of_files = self.args.get(
            "limit_number_of_files", 100)
        self._limit_bytes = self.args.get("limit_number_bytes", 10000000)
        # setup sane defaults

        self._cleanup_service = self.args.get("service", None)
        self._cleanup_sensor = self.args.get("sensor", None)

        self._handle = self.listen_state(self.trigger_cleanup_callback, self._cleanup_sensor)

    def trigger_cleanup_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback trigger_cleanup_callback from {}:{} {}->{}".format(entity, attribute, old, new))

        current_number_of_files = self.get_state(entity, attribute = "number_of_files")
        current_bytes = self.get_state(entity, attribute = "bytes")

        if(current_number_of_files < self._limit_number_of_files):
            self.log("Skipping cleanup because number_of_files is below limit {} < {}".format(current_number_of_files, self._limit_number_of_files))
            return

        if(current_bytes < self._limit_bytes):
            self.log("Skipping cleanup because bytes is below limit {} < {}".format(current_bytes, self._limit_bytes))
            return

        self.log("Calling service {}".format(self._cleanup_service))

        self.call_service(self._cleanup_service)
