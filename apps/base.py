import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, timezone, timedelta
import json
import hashlib
import inspect

class BaseApp(hass.Hass):
    def initialize(self):
        self.log(f"Initializing {self.__class__.__name__}")

        # setup sane defaults
        self._opening_sensors = self.args.get("opening_sensors", [])
        self._motion_sensors = self.args.get("motion_sensors", [])
        self._illumination_sensors = self.args.get("illumination_sensors", [])
        self._device_trackers = self.args.get("device_trackers", [])
        self._media_players = self.args.get("media_players", [])

        self._vacation_control = self.args.get("vacation_control", None)
        self._guest_control = self.args.get("guest_control", None)
        self._alarm_control_panel = self.args.get("alarm_control_panel", None)
        self._opening_timeout = self.args.get("opening_timeout", 30)
        self._motion_timeout = self.args.get("motion_timeout", 60*5)
        self._tracker_timeout = self.args.get("tracker_timeout", 60)
        self._vacation_timeout = self.args.get("vacation_timeout", 60)

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
        self._night_end = self.args.get("night_end", "06:30:00")

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
        self.log(f"Got vacation timeout {self._vacation_timeout}")
        self.log(f"Got {self.count_home_device_trackers()} device_trackers home and {self.count_not_home_device_trackers()} device_trackers not home")
        self.log(f"Got guest_mode {self.in_guest_mode()}")
        self.log(f"Got vacation_mode {self.in_vacation_mode()}")
        self.log(f"Got language {self._language}")
        self.log(f"Got alexa media devices {self._alexa_media_devices}")
        self.log(f"Got alexa voice monkeys {self._alexa_monkeys}")
        self.log(f"Got awtrix prefixes {self._awtrix_prefixes}")

    def log(self, message, level="INFO", *args, **kwargs):
        """Custom log function to ensure UTF-8 output and handle args/kwargs properly."""

        # Format the message if args are passed
        if args or kwargs:
            message = message % (*args, *kwargs.values())

        # Ensure the message is a string before passing it to super().log()
        super().log(str(message), level=level, ascii_encode=False)

    def get_utc_time(self):
        """Returns the current UTC time"""
        return datetime.now(timezone.utc)

    def log_event(self, message):
        """Logs a message with the app name"""
        self.log(f"[{self.__class__.__name__}] {message}")

    def is_time_in_night_window(self):
        return self.now_is_between(self._night_start, self._night_end)

    def in_silent_mode(self):
        if self._silent_control is None:
            return False
        if self.get_state(self._silent_control) == 'on':
            return True
        else:
            return False

    def get_seconds_until_night_end(self):
        now = datetime.now()
        night_end_time = datetime.strptime(self._night_end, "%H:%M:%S").time()
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

    def count_opening_sensors(self, state):
        if state == 'any':
            return len(self._opening_sensors)

        count = 0
        for sensor in self._opening_sensors:
            if self.get_state(sensor) == state:
                count = count + 1
            elif self.get_seconds_since_update(sensor) is not None and self.get_seconds_since_update(sensor) < self._opening_timeout:
                count = count + 1
        return count

    def count_on_opening_sensors(self):
        return self.count_opening_sensors("on")

    def count_off_opening_sensors(self):
        return self.count_opening_sensors("off")

    def count_motion_sensors(self, state):
        if state == 'any':
            return len(self._motion_sensors)

        count = 0
        for sensor in self._motion_sensors:
            if self.get_state(sensor) == state:
                count = count + 1
            elif self.get_seconds_since_update(sensor) is not None and self.get_seconds_since_update(sensor) < self._motion_timeout:
                count = count + 1
        return count

    def get_last_motion(self):
        last_motion = None
        for sensor in self._motion_sensors:
            if self.get_state(sensor) == "on":
                return 0
            if last_motion == None:
                # FIXME
                last_motion = self.get_seconds_since_update(sensor)
            elif self.get_seconds_since_update(sensor) is not None and self.get_seconds_since_update(sensor) < last_motion:
                last_motion = self.get_seconds_since_update(sensor)
        return last_motion

    def count_on_motion_sensors(self):
        return self.count_motion_sensors("on")

    def count_off_motion_sensors(self):
        return self.count_motion_sensors("off")

    def get_seconds_since_update(self, entity):
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
        self.log("Recording interal change")
        self._internal_change_timestamp = datetime.now(timezone.utc)
        self._internal_change_count = self._internal_change_count + 1

    def record_external_change(self):
        self.log("Recording external change")
        self._external_change_timestamp = datetime.now(timezone.utc)
        self._external_change_count = self._external_change_count + 1

    def reset_internal_change_records(self):
        self.log("Reseting interal change records")
        self._internal_change_timestamp = None
        self._internal_change_count = 0

    def reset_external_change_records(self):
        self.log("Reseting external change records")
        self._external_change_timestamp = None
        self._external_change_count = 0

    def get_last_internal_change(self):
        return self._internal_change_timestamp

    def get_last_external_change(self):
        return self._external_change_timestamp

    def get_external_change_timeout(self):
        return self._external_change_timeout

    def get_internal_change_timeout(self):
        return self._internal_change_timeout

    def is_current_change_external(self):
        last_internal_change = self.get_last_internal_change()

        if last_internal_change is None:
            self.log("No internal change detected. Assuming the current change is external.", level = "DEBUG")
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
            self.log(f"Current change is NOT external. Wait {remaining_time:.2f} more seconds.", level = "DEBUG")
            return False

        self.log("Current change is considered external.")
        return True

    def is_last_change_external(self):
        if (self.get_last_external_change() == None):
            return False
        if (self.get_last_internal_change() == None):
            return True
        if (self.get_last_external_change() > self.get_last_internal_change()):
            return True

    def is_internal_change_allowed(self):
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

        self.log("Internal change is now allowed.")
        return True

    def get_remaining_seconds_before_internal_change_is_allowed(self):
        if not self.is_last_change_external():
            self.log("No external change detected. Remaining time: 0 seconds")
            return 0

        now = datetime.now(timezone.utc).replace(microsecond=0)  # Remove milliseconds
        last_change = self.get_last_external_change()

        if last_change is None:
            self.log("No record of last external change. Returning full timeout.", level="WARNING")
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


    def count_media_players(self, state, sources=None):
        self.log(f"Count media players in state {state} and sources {sources}", level="DEBUG")
        if state == 'any':
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
        return self.count_media_players("playing")

    def count_on_media_players(self):
        return self.count_media_players("on")

    def count_off_media_players(self):
        return self.count_media_players("off")

    def count_lights(self, state):
        self.log(f"count lights in state {state}", level = "DEBUG")
        if state == 'any':
            return len(self._lights)

        count = 0
        for sensor in self._lights:
            self.log(f"light {sensor} is in state {self.get_state(sensor)}", level = "DEBUG")
            if self.get_state(sensor) == state:
                count = count + 1

        self.log(f"found {count} lights in state {state}", level = "DEBUG")
        return count

    def count_on_lights(self):
        return self.count_lights("on")

    def count_off_lights(self):
        return self.count_motion("off")

    def count_device_trackers(self, state):
        self.log(f"count device trackers in state {state}", level = "DEBUG")
        if state == 'any':
            return len(self._device_trackers)

        count = 0
        for sensor in self._device_trackers:
            self.log(f"device tracker {sensor} is in state {self.get_state(sensor)}", level = "DEBUG")
            if self.get_state(sensor) == state:
                count = count + 1

        self.log(f"found {count} device trackers in state {state}", level = "DEBUG")
        return count

    def count_home_device_trackers(self):
        return self.count_device_trackers("home")

    def count_not_home_device_trackers(self):
        return self.count_device_trackers("not_home")

    def is_somebody_at_home(self):
        if self.count_home_device_trackers() > 0:
            self.log("found device trackers", level = "DEBUG")
            return True
        if self.in_guest_mode():
            self.log("found geust mode", level = "DEBUG")
            return True
        if self.in_vacation_mode():
            self.log("found vacation mode", level = "DEBUG")
            return True
        return False

    def is_nobody_at_home(self):
        return not self.is_somebody_at_home()

    def in_guest_mode(self):
        if self._guest_control is None:
            return False
        if self.get_state(self._guest_control) == 'on':
            return True
        else:
            return False

    def in_vacation_mode(self):
        if self._vacation_control is None:
            return False
        if self.get_state(self._vacation_control) == 'on':
            return True
        else:
            return False

    def is_alarm_armed_away(self):
        return self.is_alarm_in_state('armed_away')

    def is_alarm_armed_home(self):
        return self.is_alarm_in_state('armed_home')

    def is_alarm_armed_night(self):
        return self.is_alarm_in_state('armed_night')

    def is_alarm_armed_vacation(self):
        return self.is_alarm_in_state('armed_vacation')

    def is_alarm_armed(self):
        return self.get_state(self._alarm_control_panel) in ['armed_away', 'armed_away', 'armed_night', 'armed_vacation']

    def is_alarm_disarmed(self):
        return self.is_alarm_in_state('disarmed')

    def is_alarm_arming(self):
        return self.is_alarm_in_state('arming')

    def is_alarm_pending(self):
        return self.is_alarm_in_state('pending')

    def is_alarm_triggered(self):
        return self.is_alarm_in_state('triggered')

    def is_alarm_in_state(self, state):
        if self._alarm_control_panel is None:
            return False
        if self.get_state(self._alarm_control_panel) == state:
            return True
        return False

    def get_alarm_state(self):
        if self._alarm_control_panel is None:
            return None
        return self.get_state(self._alarm_control_panel)

    def below_min_elevation(self, value = None):
        if isinstance(value, int) or isinstance(value, float):
            if value < self._min_elevation:
                return True
            return False

        if self.get_state("sun.sun", attribute = "elevation") < self._min_elevation:
            return True
        return False

    def below_min_illumination(self, value = None):
        if isinstance(value, int) or isinstance(value, float):
            if value < self._min_illumination:
                return True
            return False

        for sensor in self._illumination_sensors:
            if self.get_state(sensor) == None:
                return True
            if self.get_state(sensor) == 'unknown':
                return True
            if self.get_state(sensor) == 'unavailable':
                return True
            if float(self.get_state(sensor)) < self._min_illumination:
                return True
        return False

    def above_max_illumination(self, value = None):
        if isinstance(value, int) or isinstance(value, float):
            if value < self._min_illumination:
                return True
            return False

        for sensor in self._illumination_sensors:
            if self.get_state(sensor) == None:
                return False
            if self.get_state(sensor) == 'unknown':
                return False
            if self.get_state(sensor) == 'unavailable':
                return False
            if float(self.get_state(sensor)) > self._max_illumination:
                return True
        return False

    def control_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        if old is None:
            return

        if old == 'unknown':
            return

        if old == 'unavailable':
            return

        if self.is_current_change_external():
            self.record_external_change()


    def notify(self, message, title=None, prio=0):
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
        if title is None:
            title = self.__class__.__name__

        for user_id in self._telegram_user_ids:
            self.log(f"Calling service telegram_bot/send_message with user_id {user_id} and message: {message}")
            self.call_service('telegram_bot/send_message',
                                title='*' + title + '*',
                                target=user_id,
                                message=message,
                                disable_notification=True)

    def notify_notify(self, message, title=None):
        if title is None:
            title = self.__class__.__name__

        for target in self._notify_targets:
            service_name = f"notify/mobile_app_{target}"
            self.log(f"Calling service {service_name} message: {message}")
            self.call_service(service_name,
                                title='*' + title + '*',
                                message=message)

    def notify_persistent(self, message, title=None):
        if title is None:
            title = self.__class__.__name__

        self.log(f"Calling service persistent_notification/create with message: {message}")
        self.call_service('persistent_notification/create',
                            title='*' + title + '*',
                            message=message)

    def notify_awtrix(self, message, app = None, duration = 60, lifetime = 600):
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
            self.log("Error: No message provided for media notification.")
            return

        self.notify_alexa_media(message, title)
        self.notify_alexa_monkey(message, title)
        self.notify_tts(message, title)

    def notify_tts(self, message, title=None, volume_level=0.35):
        if len(self._tts_devices) > 0:
            language = 'en-US'
            if self._language == 'german':
                language = 'de-DE'
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
        if title is None:
            title = self.__class__.__name__

        if len(self._alexa_media_devices) > 0:
            data = {"type":"announce","method":"all"}
            self.log(f"Calling service notify/alexa_media with message: {message}")
            self.call_service(
                "notify/alexa_media", message=message, title=title, data=data, target=self._alexa_media_devices)

    def notify_alexa_monkey(self, message, title=None):
        if title is None:
            title = self.__class__.__name__

        if len(self._alexa_monkeys) > 0:
            for monkey in self._alexa_monkeys:
                data = {"announcement":message,"monkey":monkey}
                self.log(f"Calling service rest_command/trigger_monkey with monkey {monkey} and message: {message}")
                self.call_service(
                    "rest_command/trigger_monkey", announcement=message, monkey=monkey)

    def translate(self, message):
        return self._translation.get(self._language, {}).get(message, f"Missing translation: {message}")
