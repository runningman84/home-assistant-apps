"""Base utilities for AppDaemon apps providing common helpers and configuration defaults.

This module provides a `BaseApp` class that other app modules inherit from. It
centralizes common configuration keys, sensible defaults, and utility helpers used
across multiple apps (e.g., motion/opening counters, night window helpers, TTS/awtrix helpers).

Common args provided by `BaseApp` (all optional unless noted):
- opening_sensors, motion_sensors, illumination_sensors, device_trackers
- vacation_control, guest_control, alarm_control_panel
- night_start, night_end, night_start_workday, night_end_workday
- notify_service, awtrix_prefixes, tts_devices
- external_change_timeout, internal_change_timeout

See module docstrings and inline examples for canonical usage and common options used across apps.
"""

import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, timezone, timedelta, date
import json
import inspect



class BaseApp(hass.Hass):
    def initialize(self):
        """Initialize BaseApp defaults and log configuration.

        This method is called by AppDaemon on startup. It reads common
        configuration options from `self.args`, sets sensible defaults on
        instance attributes, and writes a short configuration summary to the
        AppDaemon log.
        """
        self.log(f"Initializing {self.__class__.__name__}")

        # setup sane defaults
        self._opening_sensors = self.args.get("opening_sensors", [])
        self._motion_sensors = self.args.get("motion_sensors", [])
        self._illumination_sensors = self.args.get("illumination_sensors", [])
        self._awake_sensors = self.args.get("awake_sensors", [])
        self._device_trackers = self.args.get("device_trackers", [])
        self._media_players = self.args.get("media_players", [])
        self._vacuum_cleaners = self.args.get("vacuum_cleaners", [])
        self._lights = self.args.get("lights", [])
        self._vacation_control = self.args.get("vacation_control", None)
        self._guest_control = self.args.get("guest_control", None)
        self._alarm_control_panel = self.args.get("alarm_control_panel", None)
        self._opening_timeout = self.args.get("opening_timeout", 30)
        self._motion_timeout = self.args.get("motion_timeout", 60*5)
        self._tracker_timeout = self.args.get("tracker_timeout", 60)
        self._vacation_timeout = self.args.get("vacation_timeout", 60)
        self._awake_timeout = self.args.get("awake_timeout", 60*15)

        self._notify_service = self.args.get("notify_service", None)
        self._notify_title = self.args.get(
            "notify_title", "AlarmSystem triggered, possible {}")
        self._telegram_user_ids = self.args.get("telegram_user_ids",[])
        self._notify_targets = self.args.get("notify_targets",[])
        self._alexa_media_devices = self.args.get("alexa_media_devices",[])
        self._alexa_monkeys = self.args.get("alexa_monkeys",[])
        self._tts_devices = self.args.get("tts_devices",[])
        self._silent_control = self.args.get("silent_control", None)


        self._awtrix_prefixes = self.args.get("awtrix_prefixes", [])
        self._awtrix_app = "hass"

        self._language = self.args.get("language","english")
        self._translation = {
            "german" : {},
            "english" : {}
        }

        self._night_start = self.args.get("night_start", "23:15:00")
        self._night_end = self.args.get("night_end", "08:30:00")
        self._night_start_workday = self.args.get("night_start_workday", "22:15:00")
        self._night_end_workday = self.args.get("night_end_workday", "06:30:00")
        self._workday_sensor = self.args.get("workday_sensor", None)
        self._workday_tomorrow_sensor = self.args.get("workday_tomorrow_sensor", None)
        self._holiday_sensor = self.args.get("holiday_sensor", None)

        self._external_change_timeout = int(self.args.get("external_change_timeout", 3600*2))
        self._internal_change_timeout = int(self.args.get("internal_change_timeout", 10))
        self._internal_change_timestamp = None
        self._external_change_timestamp = None
        self._internal_change_count = 0
        self._external_change_count = 0

        # log current config
        self.log(f"Got opening sensors {self._opening_sensors}")
        self.log(f"Got opening timeout {self._opening_timeout}")
        self.log(f"Got motion sensors {self._motion_sensors}")
        self.log(f"Got motion timeout {self._motion_timeout}")
        self.log(f"Got device trackers {self._device_trackers}")
        self.log(f"Got tracker timeout {self._tracker_timeout}")
        self.log(f"Got vacuum cleaners {self._vacuum_cleaners}")
        self.log(f"Got vacation timeout {self._vacation_timeout}")
        self.log(f"Got awake sensors {self._awake_sensors}")
        self.log(f"Got awake timeout {self._awake_timeout}")
        self.log(f"Got {self.count_home_device_trackers()} device_trackers home and {self.count_not_home_device_trackers()} device_trackers not home")
        self.log(f"Got guest_mode {self.in_guest_mode()}")
        self.log(f"Got vacation_mode {self.in_vacation_mode()}")
        self.log(f"Got language {self._language}")
        self.log(f"Got alexa media devices {self._alexa_media_devices}")
        self.log(f"Got alexa voice monkeys {self._alexa_monkeys}")
        self.log(f"Got awtrix prefixes {self._awtrix_prefixes}")
        self.log(f"Got night start {self._night_start}")
        self.log(f"Got night end {self._night_end}")
        self.log(f"Got night start workday {self._night_start_workday}")
        self.log(f"Got night end workday {self._night_end_workday}")

    def log(self, message, level="INFO", *args, **kwargs):
        """Custom log function to ensure UTF-8 output and handle args/kwargs properly."""
        # Format the message if args are passed
        if args or kwargs:
            message = message % (*args, *kwargs.values())

        # Ensure the message is a string before passing it to super().log()
        super().log(str(message), level=level, ascii_encode=False)

    def get_utc_time(self):
        """Return the current UTC datetime.

        Returns:
            datetime: timezone-aware UTC datetime.
        """
        return datetime.now(timezone.utc)

    def log_event(self, message):
        """
        Log a message prefixed with the app class name.

        Args:
            message (str): message to log.
        """
        self.log(f"[{self.__class__.__name__}] {message}")

    def is_workday_today(self):
        """Return True if today is considered a workday.

        If a workday sensor is configured it will be used; otherwise the
        weekday (Mon-Fri) is used as a fallback. Holidays override workday.

        Returns:
            bool: True when today is a workday.
        """
        if self.is_holiday_today():
            return False
        if self._workday_sensor is None:
            self.log("using workday fallback for today", level = "DEBUG")
            today = date.today()
            return today.weekday() < 5  # Monday-Friday are workdays
        self.log(f"workday today state {self.get_state(self._workday_sensor)}", level = "DEBUG")
        return self.get_state(self._workday_sensor) == 'on'

    def is_workday_tomorrow(self):
        """Return True if tomorrow is considered a workday.

        Uses a configured sensor when present; otherwise uses the weekday
        fallback (Mon-Fri).

        Returns:
            bool: True when tomorrow is a workday.
        """
        if self._workday_tomorrow_sensor is None:
            self.log("using workday fallback for tomorrow", level = "DEBUG")
            tomorrow = date.today() + timedelta(days=1)
            return tomorrow.weekday() < 5  # Returns True for Monday-Friday
        self.log(f"workday tomorrow state {self.get_state(self._workday_tomorrow_sensor)}", level = "DEBUG")
        return self.get_state(self._workday_tomorrow_sensor) == 'on'

    def is_holiday_today(self):
        """Return True if today is a holiday according to the configured sensor.

        Returns:
            bool: True when the holiday sensor (if configured) is 'on'.
        """
        if self._holiday_sensor is None:
            return False
        return self.get_state(self._holiday_sensor) == 'on'

    def get_night_times(self):
        """Return the configured night start/end times considering workdays.

        Chooses workday-specific night windows when appropriate.

        Returns:
            tuple(str, str): night_start, night_end in 'HH:MM:SS' format.
        """
        today_workday = self.is_workday_today()
        tomorrow_workday = self.is_workday_tomorrow()

        self.log(f"today_workday {today_workday} tomorrow_workday {tomorrow_workday}", level = "DEBUG")

        night_start = self._night_start_workday if tomorrow_workday else self._night_start
        night_end = self._night_end_workday if today_workday else self._night_end
        return night_start, night_end

    def is_time_in_night_window(self):
        """Return True if the current time is within the configured night window.

        Uses `get_night_times` to consider workday-specific windows.
        """
        night_start, night_end = self.get_night_times()
        self.log(f"night start {night_start} night end {night_end}", level = "DEBUG")
        return self.now_is_between(night_start, night_end)

    def in_silent_mode(self):
        """Return True if the configured silent control entity is enabled.

        Returns:
            bool: silent state.
        """
        if self._silent_control is None:
            return False
        if self.get_state(self._silent_control) == 'on':
            return True
        else:
            return False

    def get_seconds_until_night_end(self):
        """Return seconds remaining until the configured night end time.

        Accounts for night windows that roll over to the next day.

        Returns:
            int: number of seconds until night end; 0 if night already ended.
        """
        now = datetime.now()
        night_start, night_end = self.get_night_times()
        night_end_time = datetime.strptime(night_end, "%H:%M:%S").time()
        night_end_datetime = datetime.combine(now.date(), night_end_time)

        # If the night end time is earlier in the day than the current time (meaning it belongs to the next day)
        if now.time() > night_end_time:
            night_end_datetime += timedelta(days=1)

        # If it's already daytime today, return 0
        if now >= night_end_datetime:
            return 0

        # Otherwise, calculate the remaining seconds
        seconds_left = int((night_end_datetime - now).total_seconds())
        return seconds_left

    def count_opening_sensors(self, state = None):
        """Count opening sensors, optionally filtered by state.

        If a state is provided, sensors that have that state OR that were updated
        recently (within opening_timeout) are counted.

        Args:
            state (str|None): optional state to filter by (e.g., 'on' or 'off').

        Returns:
            int: number of sensors matching criteria.
        """
        if state is None:
            return len(self._opening_sensors)

        count = 0
        for sensor in self._opening_sensors:
            if self.get_state(sensor) == state:
                count = count + 1
            elif self.get_seconds_since_update(sensor) is not None and self.get_seconds_since_update(sensor) < self._opening_timeout:
                count = count + 1
        return count

    def count_on_opening_sensors(self):
        """
        Count opening sensors currently in the 'on' state.

        Returns:
            int: number of opening sensors in state 'on'.
        """
        return self.count_opening_sensors("on")

    def count_off_opening_sensors(self):
        """
        Count opening sensors currently in the 'off' state.

        Returns:
            int: number of opening sensors in state 'off'.
        """
        return self.count_opening_sensors("off")

    def count_motion_sensors(self, state = None):
        """Count motion sensors, optionally filtered by state.

        If a state is provided, sensors that have that state OR that were updated
        recently (within motion_timeout) are counted.

        Args:
            state (str|None): optional state to filter by.

        Returns:
            int: matching sensor count.
        """
        if state is None:
            return len(self._motion_sensors)

        count = 0
        for sensor in self._motion_sensors:
            if self.get_state(sensor) == state:
                count = count + 1
            elif self.get_seconds_since_update(sensor) is not None and self.get_seconds_since_update(sensor) < self._motion_timeout:
                count = count + 1
        return count

    def get_last_motion(self):
        """Return seconds since the most recent motion event among configured sensors.

        Returns 0 immediately if any motion sensor is currently 'on'. Otherwise
        returns the smallest seconds-since-update value found or None if none
        are available.

        Returns:
            float|None: seconds since last motion or None.
        """
        last_motion = None
        for sensor in self._motion_sensors:
            if self.get_state(sensor) == "on":
                return 0
            if last_motion is None:
                # FIXME
                last_motion = self.get_seconds_since_update(sensor)
            elif self.get_seconds_since_update(sensor) is not None and self.get_seconds_since_update(sensor) < last_motion:
                last_motion = self.get_seconds_since_update(sensor)
        return last_motion

    def count_on_motion_sensors(self):
        """
        Count motion sensors currently in the 'on' state.

        Returns:
            int: number of motion sensors in state 'on'.
        """
        return self.count_motion_sensors("on")

    def count_off_motion_sensors(self):
        """
        Count motion sensors currently in the 'off' state.

        Returns:
            int: number of motion sensors in state 'off'.
        """
        return self.count_motion_sensors("off")

    def get_seconds_since_update(self, entity):
        """Return seconds elapsed since the entity's last_updated attribute.

        Args:
            entity (str): entity_id to query.

        Returns:
            float|None: seconds since last update or None if unavailable.
        """
        last_updated_str = self.get_state(entity, attribute="last_updated")

        if last_updated_str:
            # Convert ISO string to datetime object
            last_updated = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))

            # Get current time in UTC
            now = datetime.now(timezone.utc)

            # Calculate time difference in seconds
            seconds_elapsed = (now - last_updated).total_seconds()

            self.log(f"{entity} was last updated {seconds_elapsed:.2f} seconds ago.", level = "DEBUG")
            return seconds_elapsed
        else:
            self.log(f"Could not retrieve last_updated for {entity}.", level = "DEBUG")
            return None

    def record_internal_change(self):
        """Record that this app made an internal change.

        Stores a timestamp and increments an internal counter used to
        distinguish internal vs external changes to entities.
        """
        self.log("Recording internal change")
        self._internal_change_timestamp = datetime.now(timezone.utc)
        self._internal_change_count = self._internal_change_count + 1

    def record_external_change(self):
        """Record that an external change was observed.

        Stores a timestamp and increments an external change counter.
        """
        self.log("Recording external change")
        self._external_change_timestamp = datetime.now(timezone.utc)
        self._external_change_count = self._external_change_count + 1

    def reset_internal_change_records(self):
        """Reset internal change records to default state."""
        self.log("Resetting internal change records")
        self._internal_change_timestamp = None
        self._internal_change_count = 0

    def reset_external_change_records(self):
        """Reset external change records to default state."""
        self.log("Resetting external change records")
        self._external_change_timestamp = None
        self._external_change_count = 0

    def get_last_internal_change(self):
        """Return the last recorded internal change timestamp (or None)."""
        return self._internal_change_timestamp

    def get_last_external_change(self):
        """Return the last recorded external change timestamp (or None)."""
        return self._external_change_timestamp

    def get_external_change_timeout(self):
        """Return the configured external change timeout in seconds."""
        return self._external_change_timeout

    def get_internal_change_timeout(self):
        """Return the configured internal change timeout in seconds."""
        return self._internal_change_timeout

    def is_current_change_external(self):
        """Return True when the current change should be considered external.

        Compares the time since the last internal change against the
        configured internal timeout to determine if a change is external.

        Returns:
            bool: True when the current change is external.
        """
        last_internal_change = self.get_last_internal_change()

        if last_internal_change is None:
            self.log("Current change is considered external. There was not any internal change recorded.", level = "DEBUG")
            return True

        # Get current time in UTC
        now = datetime.now(timezone.utc)

        # Calculate seconds since the last internal change
        seconds_ago = (now - last_internal_change).total_seconds()

        # Get the timeout value
        timeout = self.get_internal_change_timeout()
        remaining_time = max(0, timeout - seconds_ago)

        # Improved logging
        self.log(f"Last internal change: {last_internal_change}, Now: {now}, Elapsed: {seconds_ago:.2f}s, Timeout: {timeout}s, Remaining: {remaining_time:.2f}s", level = "DEBUG")

        # Determine if the change is external
        if remaining_time > 0:
            self.log(f"Current change is considered internal. Last recorded internal change was recorded {seconds_ago:.2f} seconds ago which is inside of timeout {timeout:.2f} window.", level = "DEBUG")
            return False

        self.log(f"Current change is considered external. Last recorded internal change was recorded {seconds_ago:.2f} seconds ago which is outside of timeout {timeout:.2f} window.", level = "DEBUG")
        return True

    def is_last_change_external(self):
        """Return True when the last recorded change was external.

        Compares timestamps of last external and last internal changes.
        """
        if self.get_last_external_change() is None:
            return False
        if self.get_last_internal_change() is None:
            return True
        if (self.get_last_external_change() > self.get_last_internal_change()):
            return True

    def is_internal_change_allowed(self):
        """Return True when an internal change (made by the app) is allowed.

        Rules:
        - If no external change was recorded, internal changes are allowed.
        - If nobody is at home and no motion is detected, internal changes are allowed.
        - Otherwise, wait for the external timeout window to expire.
        """
        if not self.is_last_change_external():
            self.log("No external change detected. Internal change is allowed.", level = "DEBUG")
            return True

        if self.is_nobody_at_home() and self.count_on_motion_sensors() == 0:
            self.log("Nobody is at home and there is no motion. Internal change is allowed.", level = "DEBUG")
            return True

        remaining_time = self.get_remaining_seconds_before_internal_change_is_allowed()

        # Determine if internal change is allowed
        if remaining_time > 0:
            self.log(f"Internal change is NOT allowed yet. Wait {remaining_time:.2f} more seconds.", level = "DEBUG")
            return False

        self.log("Internal change is now allowed.", level = "DEBUG")
        return True

    def get_remaining_seconds_before_internal_change_is_allowed(self):
        """Return the remaining seconds until internal changes are allowed.

        If there is no recent external change this returns 0. Otherwise it
        computes timeout - elapsed_seconds and returns a non-negative value.
        """
        if not self.is_last_change_external():
            self.log("No external change detected. Remaining time: 0 seconds", level="DEBUG")
            return 0

        now = datetime.now(timezone.utc).replace(microsecond=0)  # Remove milliseconds
        last_change = self.get_last_external_change()

        if last_change is None:
            self.log("No record of last external change. Returning full timeout.", level="DEBUG")
            return self.get_external_change_timeout()

        last_change = last_change.replace(microsecond=0)  # Remove milliseconds

        seconds_ago = max(0, (now - last_change).total_seconds())
        timeout = self.get_external_change_timeout()

        if timeout is None or timeout < 0:
            self.log(f"Invalid timeout value: {timeout}. Defaulting to 0.", level="WARNING")
            return 0

        remaining_time = max(0, timeout - seconds_ago)

        self.log(f"Last external change: {last_change}, Now: {now}, "
                f"Elapsed: {seconds_ago}s, Timeout: {timeout}s, Remaining: {remaining_time}s",
                level="DEBUG")

        return remaining_time


    def count_media_players(self, state=None, sources=None):
        """Count media players optionally filtered by state and allowed sources.

        Args:
            state (str|None): state to filter by (e.g., 'playing', 'on').
            sources (list|None): optional list of source names to filter by.

        Returns:
            int: number of matching media players.
        """
        self.log(f"Count media players in state {state} and sources {sources}", level="DEBUG")
        if state is None:
            return len(self._media_players)

        if sources is None:
            sources = []

        count = 0
        for sensor in self._media_players:
            self.log(f"Media player {sensor} is in state {self.get_state(sensor)}", level="DEBUG")
            if self.get_state(sensor) == state:
                if len(sources) == 0:
                    count = count + 1
                else:
                    if self.get_state(sensor, attribute = "source") in sources:
                        count = count + 1

        self.log(f"found {count} media players in state {state} and sources {sources}", level = "DEBUG")
        return count

    def count_playing_media_players(self):
        """
        Count media players currently in the "playing" state.

        Returns:
            int: number of media players in state 'playing'.
        """
        return self.count_media_players("playing")

    def count_on_media_players(self):
        """
        Count media players currently turned on.

        Returns:
            int: number of media players in state 'on'.
        """
        return self.count_media_players("on")

    def count_off_media_players(self):
        """
        Count media players currently turned off.

        Returns:
            int: number of media players in state 'off'.
        """
        return self.count_media_players("off")

    def count_vacuum_cleaners(self, state=None):
        """
        Count vacuum cleaners, optionally filtered by state.

        Args:
            state (str|None): optional state to filter by (e.g., 'cleaning', 'docked').

        Returns:
            int: number of vacuum cleaners matching the state or total when state is None.
        """
        self.log(f"Count vacuum cleaners in state {state}", level="DEBUG")
        if state is None:
            return len(self._vacuum_cleaners)

        count = 0
        for sensor in self._vacuum_cleaners:
            self.log(f"Vacuum cleaner {sensor} is in state {self.get_state(sensor)}", level="DEBUG")
            if self.get_state(sensor) == state:
                count = count + 1

        self.log(f"found {count} vacuum cleaners in state {state}", level = "DEBUG")
        return count

    def count_cleaning_vacuum_cleaners(self):
        """
        Count vacuum cleaners currently cleaning.

        Returns:
            int: number of vacuum cleaners in state 'cleaning'.
        """
        return self.count_vacuum_cleaners("cleaning")

    def count_docked_vacuum_cleaners(self):
        """
        Count vacuum cleaners currently docked.

        Returns:
            int: number of vacuum cleaners in state 'docked'.
        """
        return self.count_vacuum_cleaners("docked")

    def count_returning_vacuum_cleaners(self):
        """
        Count vacuum cleaners that are currently returning to dock.

        Returns:
            int: number of vacuum cleaners in state 'returning'.
        """
        return self.count_vacuum_cleaners("returning")

    def count_lights(self, state = None):
        """
        Count configured lights, optionally filtered by state.

        Args:
            state (str|None): optional state to filter by (e.g., 'on' or 'off').

        Returns:
            int: number of lights matching the state or total when state is None.
        """
        self.log(f"count lights in state {state}", level = "DEBUG")
        if state is None:
            return len(self._lights)

        count = 0
        for sensor in self._lights:
            self.log(f"light {sensor} is in state {self.get_state(sensor)}", level = "DEBUG")
            if self.get_state(sensor) == state:
                count = count + 1

        self.log(f"found {count} lights in state {state}", level = "DEBUG")
        return count

    def count_on_lights(self):
        """
        Count lights that are currently on.

        Returns:
            int: number of lights in state 'on'.
        """
        return self.count_lights("on")

    def count_off_lights(self):
        """
        Count lights that are currently off.

        Returns:
            int: number of lights in state 'off'.
        """
        return self.count_lights("off")

    def count_device_trackers(self, state = None):
        """
        Count device trackers, optionally filtered by state.

        Args:
            state (str|None): optional state to filter by (e.g., 'home' or 'not_home').

        Returns:
            int: number of device trackers matching the state or total when state is None.
        """
        self.log(f"count device trackers in state {state}", level = "DEBUG")
        if state is None:
            return len(self._device_trackers)

        count = 0
        for sensor in self._device_trackers:
            self.log(f"device tracker {sensor} is in state {self.get_state(sensor)}", level = "DEBUG")
            if self.get_state(sensor) == state:
                count = count + 1

        self.log(f"found {count} device trackers in state {state}", level = "DEBUG")
        return count

    def count_home_device_trackers(self):
        """
        Count device trackers reporting 'home'.

        Returns:
            int: number of device trackers in state 'home'.
        """
        return self.count_device_trackers("home")

    def count_not_home_device_trackers(self):
        """
        Count device trackers reporting 'not_home'.

        Returns:
            int: number of device trackers in state 'not_home'.
        """
        return self.count_device_trackers("not_home")

    def count_awake_sensors(self, state = None):
        """
        Count 'awake' sensors, optionally filtered by state.

        Args:
            state (str|None): optional state to filter by (e.g., 'on' or 'off').

        Returns:
            int: number of awake sensors matching the state or total when state is None.
        """
        self.log(f"count awake sensors in state {state}", level = "DEBUG")
        if state is None:
            return len(self._awake_sensors)

        count = 0
        for sensor in self._awake_sensors:
            self.log(f"awake sensor {sensor} is in state {self.get_state(sensor)}", level = "DEBUG")
            if self.get_state(sensor) == state:
                count = count + 1

        self.log(f"found {count} awake sensor in state {state}", level = "DEBUG")
        return count

    def count_on_awake_sensors(self):
        """
        Count 'awake' sensors that are on.

        Returns:
            int: number of awake sensors in state 'on'.
        """
        return self.count_awake_sensors("on")

    def count_off_awake_sensors(self):
        """
        Count 'awake' sensors that are off.

        Returns:
            int: number of awake sensors in state 'off'.
        """
        return self.count_awake_sensors("off")

    def is_somebody_awake(self):
        """
        Determine whether at least one 'awake' sensor is active.

        Returns:
            bool: True if any awake sensor is 'on', otherwise False.
        """
        if self.count_on_awake_sensors() > 0:
            return True
        return False

    def is_nobody_awake(self):
        """
        Determine whether no 'awake' sensors are active.

        Returns:
            bool: True if no awake sensor is 'on', otherwise False.
        """
        if self.count_on_awake_sensors() == 0:
            return True
        return False

    def is_somebody_at_home(self):
        """
        Determine whether someone is considered at home.

        Logic:
          - If any device_tracker reports 'home' -> True
          - If guest mode is active -> True
          - If vacation mode is active -> False (explicit override)

        Returns:
            bool: True if someone is at home, False otherwise.
        """
        if self.count_home_device_trackers() > 0:
            self.log("found device trackers", level = "DEBUG")
            return True
        if self.in_guest_mode():
            self.log("found guest mode", level = "DEBUG")
            return True
        if self.in_vacation_mode():
            self.log("found vacation mode", level = "DEBUG")
            return False
        return False

    def is_nobody_at_home(self):
        """
        Convenience negation of `is_somebody_at_home`.

        Returns:
            bool: True if nobody is considered at home, False otherwise.
        """
        return not self.is_somebody_at_home()

    def in_guest_mode(self):
        """
        Check whether the system is in guest mode.

        Returns:
            bool: True if guest control entity is set and 'on', otherwise False.
        """
        if self._guest_control is None:
            return False
        if self.get_state(self._guest_control) == 'on':
            return True
        else:
            return False

    def in_vacation_mode(self):
        """
        Check whether the system is in vacation mode.

        Returns:
            bool: True if vacation control entity is set and 'on', otherwise False.
        """
        if self._vacation_control is None:
            return False
        if self.get_state(self._vacation_control) == 'on':
            return True
        else:
            return False

    def is_alarm_armed_away(self):
        """
        Convenience check for alarm 'armed_away' state.

        Returns:
            bool: True if the alarm is 'armed_away'.
        """
        return self.is_alarm_in_state('armed_away')

    def is_alarm_armed_home(self):
        """
        Convenience check for alarm 'armed_home' state.

        Returns:
            bool: True if the alarm is 'armed_home'.
        """
        return self.is_alarm_in_state('armed_home')

    def is_alarm_armed_night(self):
        """
        Convenience check for alarm 'armed_night' state.

        Returns:
            bool: True if the alarm is 'armed_night'.
        """
        return self.is_alarm_in_state('armed_night')

    def is_alarm_armed_vacation(self):
        """
        Convenience check for alarm 'armed_vacation' state.

        Returns:
            bool: True if the alarm is 'armed_vacation'.
        """
        return self.is_alarm_in_state('armed_vacation')

    def is_alarm_armed(self):
        """
        Check whether the alarm is in any armed state.

        Note: this method considers common armed states. If no alarm control
        entity is configured this will raise (expected upstream to handle).

        Returns:
            bool: True if the alarm is in an armed state, otherwise False.
        """
        return self.get_state(self._alarm_control_panel) in ['armed_away', 'armed_home', 'armed_night', 'armed_vacation']

    def is_alarm_disarmed(self):
        """
        Convenience check for alarm 'disarmed' state.

        Returns:
            bool: True if the alarm is 'disarmed'.
        """
        return self.is_alarm_in_state('disarmed')

    def is_alarm_arming(self):
        """
        Convenience check for alarm 'arming' state.

        Returns:
            bool: True if the alarm is 'arming'.
        """
        return self.is_alarm_in_state('arming')

    def is_alarm_pending(self):
        """
        Convenience check for alarm 'pending' state.

        Returns:
            bool: True if the alarm is 'pending'.
        """
        return self.is_alarm_in_state('pending')

    def is_alarm_triggered(self):
        """
        Convenience check for alarm 'triggered' state.

        Returns:
            bool: True if the alarm is 'triggered'.
        """
        return self.is_alarm_in_state('triggered')

    def is_alarm_in_state(self, state):
        """
        Generic check for whether the alarm control panel is in a given state.

        Args:
            state (str): alarm state to check (e.g. 'armed_home', 'disarmed').

        Returns:
            bool: True if alarm control panel exists and matches the state.
        """
        if self._alarm_control_panel is None:
            return False
        if self.get_state(self._alarm_control_panel) == state:
            return True
        return False

    def get_alarm_state(self):
        """
        Return the current state of the configured alarm control panel.

        Returns:
            str|None: current alarm state or None if no alarm panel configured.
        """
        if self._alarm_control_panel is None:
            return None
        return self.get_state(self._alarm_control_panel)

    def below_min_elevation(self, value = None):
        """
        Check whether a numeric elevation is below the configured minimum.

        If `value` is provided (int/float) it will be compared directly. If
        not provided the current sun elevation (entity 'sun.sun' attribute
        'elevation') is queried and compared.

        Args:
            value (int|float|None): optional elevation value to compare.

        Returns:
            bool: True if the elevation is below the configured minimum.
        """
        if isinstance(value, int) or isinstance(value, float):
            if value < self._min_elevation:
                return True
            return False

        if self.get_state("sun.sun", attribute = "elevation") < self._min_elevation:
            return True
        return False

    def below_min_illumination(self, value = None):
        """
        Determine whether illumination is below the configured threshold.

        If `value` is provided (int/float) it is compared directly. If not,
        the configured illumination sensors are queried; missing/unknown/
        unavailable readings are considered below threshold.

        Args:
            value (int|float|None): optional illumination value to compare.

        Returns:
            bool: True if illumination is below the configured minimum.
        """
        if isinstance(value, int) or isinstance(value, float):
            if value < self._min_illumination:
                return True
            return False

        for sensor in self._illumination_sensors:
            if self.get_state(sensor) is None:
                return True
            if self.get_state(sensor) == 'unknown':
                return True
            if self.get_state(sensor) == 'unavailable':
                return True
            if float(self.get_state(sensor)) < self._min_illumination:
                return True
        return False

    def above_max_illumination(self, value = None):
        """
        Determine whether illumination is above the configured maximum.

        If `value` is provided (int/float) it is compared directly. If not,
        the configured illumination sensors are queried; missing/unknown/
        unavailable readings are treated as non-above-threshold.

        Args:
            value (int|float|None): optional illumination value to compare.

        Returns:
            bool: True if illumination is above the configured maximum.
        """
        if isinstance(value, int) or isinstance(value, float):
            if value < self._min_illumination:
                return True
            return False

        for sensor in self._illumination_sensors:
            if self.get_state(sensor) is None:
                return False
            if self.get_state(sensor) == 'unknown':
                return False
            if self.get_state(sensor) == 'unavailable':
                return False
            if float(self.get_state(sensor)) > self._max_illumination:
                return True
        return False

    def control_change_callback(self, entity, attribute, old, new, kwargs):
        """
        Generic callback for control state changes.

        This method logs the change and ignores transitions from or to
        None/unknown/unavailable. If the change appears to originate from
        an external caller the external change is recorded to avoid
        reacting to our own control actions.

        Args:
            entity (str): entity id that changed.
            attribute (str): attribute name that changed.
            old (str|None): previous state value.
            new (str|None): new state value.
            kwargs (dict): additional keyword args passed by AppDaemon.
        """
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        if old in (None, 'unknown', 'unavailable'):
            self.log(f"Ignoring change because old state is {old}")
            return

        if new in (None, 'unknown', 'unavailable'):
            self.log(f"Ignoring change because new state is {new}")
            return

        if self.is_current_change_external():
            self.record_external_change()

    def notify(self, message, title=None, prio=0):
        """
        Top-level notification helper that dispatches messages to configured targets.

        Behavior:
        - Respects night/silent windows for media output.
        - Sends messages to media (TTS/Alexa), Telegram and mobile notify targets.
        - Creates a persistent notification and uses highest-priority channels when prio == 0.

        Args:
            message (str): message text to send.
            title (str|None): optional title/prefix. Defaults to class name where used.
            prio (int): priority level (0 = urgent, 1 = normal, 2 = debug).
        """
        # prio
        # 0 = urgent
        # 1 = other
        # 2 = debug
        if self.is_time_in_night_window() and prio > 0:
            self.log("Ignoring notify alexa due to sleep time")
        else:
            self.notify_media(message = message, title = title, prio = prio)

        self.notify_telegram(message, title)
        self.notify_notify(message, title)

        if prio == 0:
            self.notify_persistent(message, title)

    def notify_telegram(self, message, title=None):
        """
        Send a short message to configured Telegram users.

        Args:
            message (str): message text to send.
            title (str|None): optional title/prefix. Defaults to class name.
        """
        if title is None:
            title = self.__class__.__name__

        for user_id in self._telegram_user_ids:
            self.log(f"Calling service telegram_bot/send_message with user_id {user_id} and message: {message}")
            self.call_service('telegram_bot/send_message',
                                service_data={
                                    "title" : f'*{title}*',
                                    "target": user_id,
                                    "message" : message,
                                    "disable_notification": True
                                }
            )

    def notify_notify(self, message, title=None):
        """
        Send a mobile notification to configured notify targets.

        Args:
            message (str): message text to send.
            title (str|None): optional title/prefix. Defaults to class name.
        """
        if title is None:
            title = self.__class__.__name__

        for target in self._notify_targets:
            service_name = f"notify/mobile_app_{target}"
            self.log(f"Calling service {service_name} message: {message}")
            self.call_service(service_name,
                                service_data={
                                    "title" : f'*{title}*',
                                    "message" : message
                                }
            )

    def notify_persistent(self, message, title=None):
        """
        Create a persistent notification in Home Assistant.

        Args:
            message (str): notification body.
            title (str|None): optional title. Defaults to class name.
        """
        if title is None:
            title = self.__class__.__name__

        self.log(f"Calling service persistent_notification/create with message: {message}")
        self.call_service('persistent_notification/create',
                                service_data={
                                    "title" : f'*{title}*',
                                    "message" : message
                                }
        )

    def notify_awtrix(self, message, app = None, duration = 60, lifetime = 600):
        """
        Send a notification to AWTRIX via MQTT custom topics.

        Args:
            message (str): text to display on AWTRIX.
            app (str|None): name of the app/topic suffix. Defaults to class name.
            duration (int): display duration in seconds.
            lifetime (int): message lifetime in seconds on AWTRIX side.
        """
        if app is None:
            app = self.__class__.__name__

        # Create the dictionary object
        notification = {
            "text": message,
            "rainbow": True,
            "duration": duration,
            "lifetime": lifetime
        }

        for prefix in self._awtrix_prefixes:
            topic = prefix + "/custom/" + app
            # Convert the dictionary to a JSON string
            notification_json = json.dumps(notification)

            self.log(f"Calling service mqtt/publish with topic {topic} and payload: {notification_json}")

            self.call_service('mqtt/publish',
                                topic=topic,
                                payload=notification_json)

    def reset_awtrix(self, app = None):
        """
        Send an empty/reset payload to AWTRIX for the given app/topic.

        Args:
            app (str|None): name of the app/topic suffix. Defaults to class name.
        """
        if app is None:
            app = self.__class__.__name__

        # Create the dictionary object
        notification = {

        }

        for prefix in self._awtrix_prefixes:
            topic = prefix + "/custom/" + app
            # Convert the dictionary to a JSON string
            notification_json = json.dumps(notification)

            self.log(f"Calling service mqtt/publish with topic {topic} and payload: {notification_json}")

            self.call_service('mqtt/publish',
                                topic=topic,
                                payload=notification_json)

    def notify_media(self, *args, **kwargs):
        """
        Dispatch a media-style notification to configured media targets.

        This method supports being invoked as a scheduled callback where the
        first positional argument may be a dict of parameters; in that case the
        dict is merged with keyword args. The message is sent to Alexa
        (announce), any configured 'alexa_monkey' REST endpoints and TTS
        media players (via the TTS integration). Silent mode suppresses
        media output.

        Args:
            *args: optional positional args (first item may be a dict of params).
            **kwargs: message/title/prio and other optional parameters.
        """
        # If a scheduled callback passed a dictionary as a positional argument,
        # merge it with any keyword arguments provided.
        if args and isinstance(args[0], dict):
            kwargs = {**args[0], **kwargs}

        # Extract parameters, using 'message' as the key (or fallback to an empty string)
        message = kwargs.get("message", "")
        title = kwargs.get("title", self.__class__.__name__)  # If title is not provided, use class name

        if self.in_silent_mode():
            self.log("No media output due to silent mode")
            return

        # Check if message is empty and log an error if so.
        if not message:
            self.error("No message provided for media notification.")
            return

        self.notify_alexa_media(message, title)
        self.notify_alexa_monkey(message, title)
        self.notify_tts(message, title)

    def notify_tts(self, message, title=None, volume_level=0.35):
        """
        Speak a message using configured TTS devices.

        This will set the volume on each configured TTS media player and then
        call the TTS service to speak the provided message. Language selection
        is controlled by `self._language` and defaults to 'en-US'.

        Args:
            message (str): message to speak.
            title (str|None): optional title (unused for TTS).
            volume_level (float): volume level to set before speaking.
        """
        if len(self._tts_devices) > 0:
            language = 'en-US'
            if self._language == 'german':
                language = 'de-DE'
            self.log(f"Setting TTS language to {language}", level="DEBUG")
            for media_player in self._tts_devices:
                self.log(f"Calling service media_player/volume_set with media_player {media_player} and voulme: {volume_level}")
                self.call_service("media_player/volume_set", entity_id=media_player, volume_level=volume_level)
                self.log(f"Calling service tts/speak with media_player {media_player} and message: {message}")
                self.call_service(
                    "tts/speak",
                    entity_id="tts.piper",
                    cache=True,
                    media_player_entity_id=media_player,
                    message=message
                )

    def notify_alexa_media(self, message, title=None):
        """
        Send an Alexa 'announce' via the Alexa Media integration.

        Args:
            message (str): message text to announce.
            title (str|None): optional title (not normally used by Alexa announce).
        """
        if title is None:
            title = self.__class__.__name__

        if len(self._alexa_media_devices) > 0:
            data = {"type":"announce","method":"all"}
            self.log(f"Calling service notify/alexa_media with message: {message}")
            self.call_service(
                "notify/alexa_media", message=message, title=title, data=data, target=self._alexa_media_devices)

    def notify_alexa_monkey(self, message, title=None):
        """
        Trigger a custom 'monkey' announcement via a REST command.

        Some setups use a small custom REST endpoint (rest_command) to trigger
        alternative Alexa behaviour; this helper calls that rest_command for
        each configured monkey target.

        Args:
            message (str): announcement text.
            title (str|None): optional title (unused by monkey command).
        """
        if title is None:
            title = self.__class__.__name__

        if len(self._alexa_monkeys) > 0:
            for monkey in self._alexa_monkeys:
                self.log(f"Calling service rest_command/trigger_monkey with monkey {monkey} and message: {message}")
                self.call_service(
                    "rest_command/trigger_monkey", announcement=message, monkey=monkey)

    def translate(self, message):
        """
        Translate a message key using the configured translation mapping.

        This looks up the given key in the `self._translation` mapping for the
        currently configured language and returns a placeholder if not found.

        Args:
            message (str): message key to translate.

        Returns:
            str: translated string or a 'Missing translation' placeholder.
        """
        return self._translation.get(self._language, {}).get(message, f"Missing translation: {message}")
