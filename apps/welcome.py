"""WelcomeControl app: announce residents and react to door/motion sensors.

Main features implemented by this module:
- Listen for the configured `door_sensor` opening event and, when it
    occurs, determine whether people are arriving ("coming") or leaving
    ("going") based on inside/outside motion sensors.
- If somebody is coming and device trackers show known people arrived
    recently, schedule a short-delayed media notification welcoming them.

Key configuration keys used by the app:
- `resident_timeout`: seconds within which a device_tracker's "home"
    state is considered a recent arrival (default: 300).
- `door_sensor`: entity id of the door binary sensor to listen for.
- `inside_motion_sensor`, `outside_motion_sensor`: motion sensors used
    to decide arrival direction.
- `device_trackers`: a list of device_tracker entity ids (provided by the
    BaseApp or app config) that are used by `get_residents()`.

Notes:
- This app does not publish MQTT payloads itself; it delegates to
    existing media/notify helpers via `notify_media` and schedules them
    using `run_in` for a short delay.
"""

import inspect
import random
from datetime import datetime

from base import BaseApp


class WelcomeControl(BaseApp):

    def initialize(self):
        """Set up WelcomeControl.

        Reads configuration values and registers a state listener for the
        configured `door_sensor` so the app can react when the door opens.

        Behaviour:
        - Stores `resident_timeout` and sensor entity ids from `self.args`.
        - Registers `sensor_change_callback` for the door sensor on the
          transition `old='off' -> new='on'` (i.e. door opened).
        """
        super().initialize()

        self._resident_timeout = self.args.get("resident_timeout", 300)
        self._cooldown_timeout = self.args.get("cooldown_timeout", 60)
        self._door_sensor = self.args.get("door_sensor")
        self._inside_motion_sensor = self.args.get("inside_motion_sensor")
        self._outside_motion_sensor = self.args.get("outside_motion_sensor")
        self._name_mapping = self.args.get("name_mapping", {})
        self._history = {}
        self._last_activity = None
        # translation support (simple mapping similar to AlarmControl)
        self._language = self.args.get("language", "german")
        self._translation = {
            "german": {
                "welcome_single": [
                    "Willkommen zurück, {names}!",
                    "Schön, dass du wieder da bist, {names}!",
                    "Hallo {names}, willkommen zuhause!",
                    "Freut mich, dich zu sehen, {names}!",
                    "Schön, dass {names} wieder da ist!",
                    "Willkommen zurück — {names} ist wieder zu Hause!",
                    "Hi {names}, willkommen zurück!",
                    "Guten Tag {names}, willkommen zuhause!",
                    "Herzlich willkommen zurück, {names}!",
                    "{names}, schön, dass du wieder da bist!"
                ],
                "welcome_multiple": [
                    "Willkommen zurück, {names}!",
                    "Schön, dass ihr wieder da seid, {names}!",
                    "Hallo {names}, willkommen zuhause!",
                    "Freut mich, euch zu sehen, {names}!",
                    "Schön, dass {names} wieder da sind!",
                    "Willkommen zurück — {names} sind wieder zu Hause!",
                    "Hi {names}, willkommen zurück!",
                    "Guten Tag {names}, willkommen zuhause!",
                    "Herzlich willkommen zurück, {names}!",
                    "{names}, schön, dass ihr wieder da seid!"
                ],
                "welcome_no_name": [
                    "Willkommen zuhause!",
                    "Schön, dass du da bist!",
                    "Hallo und willkommen!",
                    "Schön, dich zu sehen!",
                    "Willkommen!"
                ],
                "farewell_single": [
                    "Auf Wiedersehen, {names}!",
                    "Tschüss {names}, bis bald!",
                    "Mach's gut, {names}!",
                    "Bis später, {names}!",
                    "Alles Gute, {names}!",
                    "Bis bald, {names}!",
                    "Schönen Tag noch, {names}!",
                    "Auf Wiedersehen und bis bald, {names}!",
                    "Tschüss und gute Reise, {names}!",
                    "Pass auf dich auf, {names}!"
                ],
                "farewell_multiple": [
                    "Auf Wiedersehen, {names}!",
                    "Tschüss {names}, bis bald!",
                    "Macht's gut, {names}!",
                    "Bis später, {names}!",
                    "Alles Gute, {names}!",
                    "Bis bald, {names}!",
                    "Schönen Tag noch, {names}!",
                    "Auf Wiedersehen und bis bald, {names}!",
                    "Tschüss und gute Reise, {names}!",
                    "Passt auf euch auf, {names}!"
                ],
                "farewell_no_name": [
                    "Auf Wiedersehen!",
                    "Tschüss!",
                    "Bis bald!",
                    "Mach's gut!",
                    "Schönen Tag noch!",
                    "Gute Reise!",
                    "Pass auf dich auf!",
                    "Wir sehen uns!",
                    "Alles Gute!",
                    "Kommt gut an!"
                ]
            },
            "english": {
                "welcome_single": [
                    "Welcome back, {names}!",
                    "Nice to have you back, {names}!",
                    "Hello {names}, welcome home!",
                    "Good to see you, {names}!",
                    "{names} is home again!",
                    "Hi {names}, welcome back!",
                    "Greetings {names}, welcome home!",
                    "Welcome home, {names}!",
                    "Glad you're back, {names}!",
                    "{names}, great to have you home!"
                ],
                "welcome_multiple": [
                    "Welcome back, {names}!",
                    "Nice to have you all back, {names}!",
                    "Hello {names}, welcome home!",
                    "Good to see you all, {names}!",
                    "{names} are home again!",
                    "Hi {names}, welcome back!",
                    "Greetings {names}, welcome home!",
                    "Welcome home, {names}!",
                    "Glad you're all back, {names}!",
                    "{names}, great to have you all home!"
                ],
                "welcome_no_name": [
                    "Welcome home!",
                    "Nice to have you here!",
                    "Hello and welcome!",
                    "Good to see you!",
                    "Welcome!"
                ],
                "farewell_single": [
                    "Goodbye, {names}!",
                    "Bye {names}, see you soon!",
                    "Take care, {names}!",
                    "See you later, {names}!",
                    "All the best, {names}!",
                    "See you soon, {names}!",
                    "Have a nice day, {names}!",
                    "Goodbye and safe travels, {names}!",
                    "Bye and take care, {names}!",
                    "Farewell, {names}!"
                ],
                "farewell_multiple": [
                    "Goodbye, {names}!",
                    "Bye {names}, see you all soon!",
                    "Take care, {names}!",
                    "See you all later, {names}!",
                    "All the best, {names}!",
                    "See you soon, {names}!",
                    "Have a nice day, {names}!",
                    "Goodbye and safe travels to you all, {names}!",
                    "Bye and take care, {names}!",
                    "Farewell, {names}!"
                ],
                "farewell_no_name": [
                    "Goodbye!",
                    "Bye!",
                    "See you soon!",
                    "Take care!",
                    "Have a nice day!",
                    "Safe travels!",
                    "All the best!",
                    "See you later!",
                    "Take care and stay well!",
                    "Have a great day!"
                ]
            }
        }

        self.log(f"Configured door_sensor: {self._door_sensor}")
        self.log(f"Configured inside_motion_sensor: {self._inside_motion_sensor}")
        self.log(f"Configured outside_motion_sensor: {self._outside_motion_sensor}")
        self.log(f"Recent residents: {self.get_residents()}")

        self.listen_state(self.sensor_change_callback, self._door_sensor,
                                new="on", old="off")

        self.log("Startup finished")

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        """Handle sensor changes (door open event) and dispatch welcome.

        When the door opens we determine the movement `direction` using
        `get_direction()`. If the direction is "coming" we query
        `get_residents()` to obtain a list of recently arrived people
        (based on device trackers and `resident_timeout`). If any residents
        are found we schedule a media notification after a short delay
        using `run_in(self.notify_media, 2, message=...)`.

        Args:
            entity (str): entity id that changed.
            attribute (str): attribute that changed.
            old (str): previous state value.
            new (str): new state value.
            kwargs (dict): additional AppDaemon kwargs.
        """
        self.log(f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        direction = self.get_direction()
        self.log(f"Movement direction: {direction}")

        if self.is_time_in_night_window():
            self.log("Night mode active; no message sent.")
            return
        
        if not self.is_alarm_disarmed():
            self.log("Alarm is not disarmed; no message sent.")
            return

        if self._last_activity is not None:
            elapsed = (datetime.now().astimezone() - self._last_activity).total_seconds()
            if elapsed < self._cooldown_timeout:
                self.log(f"Skipping message due to recent activity {elapsed}s ago.")
                return

        if direction == "coming":
            residents = self.get_residents()
            self.log(f"Recent residents: {residents}")
            self.log("Detected coming movement; sending welcome message.")
            # Choose a single template so both audio and text use the same
            # sentence structure, then format it twice: once with mapped
            # names for better TTS and once with unmapped/display names for
            # text output.
            num_residents = len(residents)
            template = self._select_template("welcome", num_residents)
            if num_residents > 0:
                audio_names = self._format_name_list(residents, mapped=True)
                text_names = self._format_name_list(residents, mapped=False)
                audio_message = template.format(names=audio_names)
                text_message = template.format(names=text_names)
            else:
                audio_message = template
                text_message = template

            self.run_in(self.notify_media, 1, message=audio_message)
            self.notify_awtrix(text_message)
            self.store_greeted_residents(residents)
            self._last_activity = datetime.now().astimezone()
        elif direction == "going":
            self.log("Detected leaving movement; sending farewell message.")
            template = self._select_template("farewell", 0)
            audio_message = template
            text_message = template
            self.notify_media(message=audio_message)
            self.notify_awtrix(text_message)
            self._last_activity = datetime.now().astimezone()

    def store_greeted_residents(self, residents):
        """Store the list of residents who were greeted recently."""
        for resident in residents:
            self._history[resident] = datetime.now().astimezone()

    def get_direction(self):
        """Determine movement direction using inside/outside motion sensors.

        Logic:
        - If inside is "on" and outside is "off": return "coming".
        - If inside is "off" and outside is "on": return "going".
        - If both are "on", compare the seconds-since-update values and
          treat the sensor with the *smaller* seconds-since-update as the
          more recent motion (that side indicates the direction).
        - Otherwise return "unknown".

        Returns:
            str: one of "coming", "going" or "unknown".
        """

        self.log("Determining movement direction using motion sensors")

        inside_motion_state = self.get_state(self._inside_motion_sensor)
        outside_motion_state = self.get_state(self._outside_motion_sensor)
        inside_motion_seconds = self.get_seconds_since_update(self._inside_motion_sensor)
        outside_motion_seconds = self.get_seconds_since_update(self._outside_motion_sensor)

        self.log(f"Inside motion sensor: {self._inside_motion_sensor} state={inside_motion_state} seconds={inside_motion_seconds}s")
        self.log(f"Outside motion sensor: {self._outside_motion_sensor} state={outside_motion_state} seconds={outside_motion_seconds}s")

        if len(self.get_residents()) > 0:
            return "coming"

        if inside_motion_state == "on" and outside_motion_state == "off":
            return "going"
        elif inside_motion_state == "off" and outside_motion_state == "on":
            return "coming"
        elif inside_motion_state == "on" and outside_motion_state == "on":
            if inside_motion_seconds < outside_motion_seconds:
                return "coming"
            else:
                return "going"
            
        return "unknown"

    def get_residents(self, filter_greeted=True):
        """Return list of device_tracker entity ids that were recently 'home'.

        The function inspects the configured `self._device_trackers` list
        and returns the entity id for each device tracker whose state is
        "home" and whose last update time is less than
        `self._resident_timeout`.

        Callers should use `get_first_name_for_resident()` to map the
        returned entity ids to human-friendly first names when needed.

        Returns:
            list[str]: list of device_tracker entity ids (possibly empty).
        """

        residents = []

        # Iterate configured device_trackers and collect recent arrivals
        for entity in self._device_trackers:
            state = self.get_state(entity)
            last_update = self.get_seconds_since_update(entity)
            if state == "home" and last_update < self._resident_timeout:
                if filter_greeted:
                    last_greeted = self._history.get(entity)
                    if last_greeted is not None:
                        elapsed = (datetime.now().astimezone() - last_greeted).total_seconds()
                        if elapsed < self._resident_timeout:
                            self.log(f"Skipping recently greeted resident {entity} (elapsed {elapsed}s)")
                            continue
                residents.append(entity)

        return residents
    
    def get_first_name_for_resident(self, entity, mapped = True):
        """Return the mapped name for a resident entity if mapping is enabled.

        Args:
            entity (str): The device_tracker entity id to resolve.
            mapped (bool): Whether to apply name mapping. Defaults to True.

        Returns:
            str: The mapped name if mapping is enabled, otherwise the first
                 token of the entity's `friendly_name`.
        """

        friendly_name = self.get_state(entity, attribute = "friendly_name")
        first_name = friendly_name.split(" ")[0]

        if mapped:
            return self._name_mapping.get(first_name, first_name)
        return first_name
    
    def _format_name_list(self, residents, mapped=True):
        """Return a natural-language comma/and-joined name list for residents."""
        names = [self.get_first_name_for_resident(r, mapped=mapped) for r in residents]
        if len(names) == 0:
            return ""
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return f"{names[0]} und {names[1]}"
        # more than two: Oxford-style with 'und' before last
        return ", ".join(names[:-1]) + f" und {names[-1]}"

    def _select_template(self, kind, num_residents):
        """Select a template string for `kind` ('welcome'|'farewell').

        `num_residents` indicates the number of residents: 0 for no names,
        1 for single visitor, or >1 for multiple visitors. This returns a
        single template string chosen from the current language's translation
        mapping, falling back to English when necessary.
        """
        language = self._language
        if num_residents == 0:
            key = f"{kind}_no_name"
        elif num_residents == 1:
            key = f"{kind}_single"
        else:
            key = f"{kind}_multiple"
        
        templates = self._translation.get(language, {}).get(key, [])
        if not templates:
            templates = self._translation.get("english", {}).get(key, ["{names}"] if num_residents > 0 else [""])
        return random.choice(templates)

    # Template lists are provided via `self._translation` in initialize().

    def create_welcome_message(self, residents=None, mapped=True):
        """Create a (slightly randomized) welcome message for the given residents.

        Args:
            residents (list[str]|None): List of resident entity ids.
            mapped (bool): whether to apply `_name_mapping` via
                `get_first_name_for_resident`.
        Returns:
            str: localized welcome message.
        """
        if residents is None:
            residents = []

        language = self._language
        if len(residents) == 0:
            templates = self._translation.get(language, {}).get("welcome_no_name", [])
            if not templates:
                # fallback to english built-in list if translation missing
                templates = self._translation.get("english", {}).get("welcome_no_name", ["Welcome!"])
            return random.choice(templates)

        names = self._format_name_list(residents, mapped=mapped)
        templates = self._translation.get(language, {}).get("welcome_with_name", [])
        if not templates:
            templates = self._translation.get("english", {}).get("welcome_with_name", ["Welcome back {names}!"])
        template = random.choice(templates)
        return template.format(names=names)

    def create_farewell_message(self, residents=None, mapped=True):
        """Create a (slightly randomized) farewell message for the given residents.

        Args:
            residents (list[str]|None): List of resident entity ids.
            mapped (bool): whether to apply `_name_mapping` via
                `get_first_name_for_resident`.
        Returns:
            str: localized farewell message.
        """
        if residents is None:
            residents = []

        language = self._language
        if len(residents) == 0:
            templates = self._translation.get(language, {}).get("farewell_no_name", [])
            if not templates:
                templates = self._translation.get("english", {}).get("farewell_no_name", ["Goodbye!"])
            return random.choice(templates)

        names = self._format_name_list(residents, mapped=mapped)
        templates = self._translation.get(language, {}).get("farewell_with_name", [])
        if not templates:
            templates = self._translation.get("english", {}).get("farewell_with_name", ["Goodbye {names}!"])
        template = random.choice(templates)
        return template.format(names=names)