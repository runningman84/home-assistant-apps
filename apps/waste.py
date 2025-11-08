"""WasteReminder app: notify occupants about upcoming waste collection events.

Main features:
- Read a calendar-style sensor for upcoming waste collection and notify via AWTRIX/TTS when collection is today/tomorrow.
- Throttles TTS messages to avoid repeated announcements and respects night windows.

Key configuration keys:
- waste_calendar: entity id of a calendar or sensor that exposes 'start_time' and 'message' attributes.
- awtrix_prefixes: optional list of AWTRIX prefixes to notify via MQTT.

Example:
```yaml
waste_reminder:
    module: waste
    class: WasteReminder
    waste_calendar: sensor.waste_calendar
    awtrix_prefixes:
        - "awtrix/home"
```

See module docstring and inline examples for usage.
"""

from base import BaseApp
import inspect
from datetime import datetime, timedelta



class WasteReminder(BaseApp):

    def initialize(self):
        super().initialize()

        # awtrix devices
        self.__awtrix_prefixes = self.args.get("awtrix_prefixes", [])
        self._waste_calendar = self.args.get("waste_calendar", None)
        self._tts_sent_today = 0
        self._tts_sent_tomorrow = 0

        # stop power if nobody is home
        if self._waste_calendar is not None:
            self.listen_state(self.sensor_change_callback,
                                self._waste_calendar)

        # Set start time to now, aligning to the next full 10-minute mark
        self.run_every(self.periodic_time_callback, "now+15", 60 * 60)

        self.log("Startup finished")

    def periodic_time_callback(self, kwargs):
        """Periodic callback that delegates to setup() to evaluate calendar state."""
        self.log(f"{inspect.currentframe().f_code.co_name}")
        self.setup()

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        """State-change listener for the waste calendar sensor; calls setup()."""
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")
        self.setup()

    def seconds_until_tomorrow(self):
        """Return number of seconds remaining until the start of the next day."""
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int((tomorrow - now).total_seconds())

    def setup(self):
        """Evaluate the configured waste calendar and notify AWTRIX/TTS when appropriate.

        The method reads 'start_time' and 'message' attributes from the
        calendar sensor and triggers AWTRIX notifications or TTS if the
        collection is today or tomorrow. It also throttles TTS messages to
        avoid repeated announcements and resets counters when nothing is
        scheduled.
        """

        if self._waste_calendar is None:
            self.log("Doing nothing waste calendar is not defined.")
            return

        # waste_state = self.get_state(self._waste_calendar)
        waste_message = self.get_state(self._waste_calendar, attribute = "message")
        waste_start_time = self.get_state(self._waste_calendar, attribute = "start_time")
        # waste_end_time = self.get_state(self._waste_calendar, attribute = "end_time")

        # Ensure waste_start_time is valid before parsing
        if waste_start_time:
            # Convert string to datetime
            collection_date = datetime.strptime(waste_start_time, "%Y-%m-%d %H:%M:%S").date()
            today = datetime.now().date()
            tomorrow = datetime.now().date() + timedelta(days=1)

            # If waste collection is tomorrow, send a notification
            if collection_date == tomorrow:
                self.notify_awtrix(f"M\u00fcllabfuhr morgen: {waste_message}", 'waste', 15, self.seconds_until_tomorrow())

                if self.is_somebody_at_home() and self._tts_sent_tomorrow < 3 and self.is_time_in_night_window() is not True:
                    self.notify_tts(f"M\u00fcllabfuhr morgen: {waste_message}")
                    self._tts_sent_tomorrow = self._tts_sent_tomorrow + 1

                return

            # If waste collection is today, send a notification
            if collection_date == today:
                self.notify_awtrix(f"M\u00fcllabfuhr heute: {waste_message}", 'waste', 15, self.seconds_until_tomorrow())

                if self.is_somebody_at_home() and self._tts_sent_today < 1 and self.is_time_in_night_window() is not True:
                    self.notify_tts(f"M\u00fcllabfuhr heute: {waste_message}")
                    self._tts_sent_today = self._tts_sent_today + 1

                return

        self._tts_sent_today = 0
        self._tts_sent_tomorrow = 0


