"""WeatherWarning app: announce or notify about weather warnings based on configured sensors.

Main features:
- Monitor current and future weather-warning sensors and announce warnings via AWTRIX/TTS.
- Track per-warning TTS counters to avoid repeated vocal alerts and respect night windows.

Key configuration keys:
- current_warn_sensor, future_warn_sensor: sensors exposing warning_count and per-warning attributes (name, headline, description, start, end).
- awtrix_prefixes: optional list of AWTRIX MQTT prefixes to publish notifications to.

Example:
```yaml
weather_warning:
    module: weather
    class: WeatherWarning
    current_warn_sensor: sensor.dwd_current
    future_warn_sensor: sensor.dwd_future
    awtrix_prefixes:
        - "awtrix/home"
```

See module docstring and inline examples for usage.
"""

from base import BaseApp
import inspect
from datetime import datetime, timezone, timedelta



class WeatherWarning(BaseApp):

    def initialize(self):
        super().initialize()

        self.log(f"is night window {self.is_time_in_night_window()}", level = "DEBUG")

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
        self.run_every(self.periodic_time_callback, "now+15", 60 * 60)

        self.log("Startup finished")

    def periodic_time_callback(self, kwargs):
        """Periodic timer handler; re-evaluates warnings and notifies if needed."""
        self.log(f"{inspect.currentframe().f_code.co_name}")
        self.handle_warnings()

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        """State-change listener for warning sensors; triggers evaluation."""
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")
        self.handle_warnings()

    def seconds_until_tomorrow(self):
        """Return seconds remaining until next midnight local time."""
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int((tomorrow - now).total_seconds())

    def seconds_until_date(self, date):
        """Return seconds from now (UTC) until the provided aware datetime.

        If 'date' is naive (no tzinfo) it is assumed to be in UTC.
        """
        now = datetime.now(timezone.utc)

        if date.tzinfo is None:  # If 'date' is naive, assume UTC
            date = date.replace(tzinfo=timezone.utc)

        return int((date - now).total_seconds())

    def get_warning_info(self, sensor, nr):
        """Return a dict of warning attributes (name, headline, description, start, end).

        The method reads sensor attributes like 'warning_{nr}_name' and parses
        the start/end timestamps to datetime objects when present.
        """
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
        """Process warnings on the given sensor and publish notifications.

        - sensor: entity id of a warning sensor
        - tts_limit: per-warning limit to vocal announcements
        - tts_counters: dict tracking how many times each warning was spoken
        - prefix: textual prefix used for AWTRIX messages and TTS
        """
        state = int(self.get_state(sensor))

        if state == 0:
            tts_counters.clear()  # Reset all counters if there are no warnings

        if state > 0:
            warnings_count = self.get_state(sensor, attribute="warning_count")

            for i in range(1, warnings_count + 1):
                warning_info = self.get_warning_info(sensor, i)

                if not warning_info["name"]:
                    continue

                # Publish AWTRIX notification and optionally speak via TTS
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