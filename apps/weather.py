from base import BaseApp
import json
import inspect
from datetime import datetime, timezone, timedelta
import time

class WeatherWarning(BaseApp):

    def initialize(self):
        super().initialize()

        # awtrix devices
        self.__awtrix_prefixes = self.args.get("awtrix_prefixes", [])
        self._current_warn_sensor = self.args.get("current_warn_sensor", None)
        self._future_warn_sensor = self.args.get("future_warn_sensor", None)
        self._tts_sent_current = 0
        self._tts_sent_future = 0

        if self._current_warn_sensor is not None:
            self.listen_state(self.sensor_change_callback,
                                self._current_warn_sensor)

        if self._future_warn_sensor is not None:
            self.listen_state(self.sensor_change_callback,
                                self._future_warn_sensor)

        # Set start time to now, aligning to the next full 10-minute mark
        self.run_every(self.perodic_time_callback, "now+15", 60 * 60)

        self.log("Startup finished")

    def perodic_time_callback(self, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name}")
        self.handle_warnings()

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")
        self.handle_warnings()

    def seconds_until_tomorrow(self):
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int((tomorrow - now).total_seconds())

    def seconds_until_date(self, date):
        now = datetime.now(timezone.utc)

        if date.tzinfo is None:  # If 'date' is naive, assume UTC
            date = date.replace(tzinfo=timezone.utc)

        return int((date - now).total_seconds())

    def get_warning_info(self, sensor, nr):
        warning_info = {
            "name": self.get_state(self._current_warn_sensor, attribute=f"warning_{nr}_name"),
            "headline": self.get_state(self._current_warn_sensor, attribute=f"warning_{nr}_headline"),
            "description": self.get_state(self._current_warn_sensor, attribute=f"warning_{nr}_description"),
            "instruction": self.get_state(self._current_warn_sensor, attribute=f"warning_{nr}_instruction"),
            "start": None,
            "end": None
        }

        warning_start_str = self.get_state(self._current_warn_sensor, attribute=f"warning_{nr}_start")
        warning_end_str = self.get_state(self._current_warn_sensor, attribute=f"warning_{nr}_end")

        if warning_start_str:
            warning_info["start"] = datetime.fromisoformat(warning_start_str)

        if warning_end_str:
            warning_info["end"] = datetime.fromisoformat(warning_end_str)

        return warning_info

    def process_warnings(self, sensor, tts_limit, tts_counters, prefix):
        state = int(self.get_state(sensor))

        if state == 0:
            tts_counters.clear()  # Reset all counters if there are no warnings

        if state > 0:
            warnings_count = self.get_state(sensor, attribute="warning_count")

            for i in range(1, warnings_count + 1):
                warning_info = self.get_warning_info(sensor, i)

                if not warning_info["name"]:
                    continue

                self.notify_awtrix(
                    f"DWD {prefix} Warnung: {warning_info['headline']}. {warning_info['description']}",
                    f"weather{i}{prefix}",
                    90,
                    self.seconds_until_date(warning_info["end"]),
                )

                # Initialize counter if not present
                if i not in tts_counters:
                    tts_counters[i] = 0

                if (
                    self.is_somebody_at_home()
                    and tts_counters[i] < tts_limit
                    and not self.is_time_in_night_window()
                ):
                    self.notify_tts(f"Wetterdienst {prefix} Warnung: {warning_info['headline']}. {warning_info['description']}")
                    tts_counters[i] += 1

    def handle_warnings(self):
        # Ensure the dictionary exists
        if not hasattr(self, "_tts_counters"):
            self._tts_counters = {
                "current": {},  # Tracks per-warning counters for current warnings
                "future": {}  # Tracks per-warning counters for future warnings
            }

        self.process_warnings(
            self._current_warn_sensor, 3, self._tts_counters["current"], "Aktuelle"
        )

        self.process_warnings(
            self._future_warn_sensor, 2, self._tts_counters["future"], "Vorab"
        )