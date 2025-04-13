import appdaemon.plugins.hass.hassapi as hass
from base import BaseApp
from datetime import datetime, timezone, timedelta
import time
import re
import inspect

#
# AlarmControl App
#
# Args:
#


class AlarmControl(BaseApp):

    def initialize(self):
        super().initialize()


        # translation
        self._language = self.args.get("language","english")
        self._translation = {
            "german" : {
                "burglar_alert": "Achtung! Einbruchsalarm!",
                "fire_alert": "Achtung! Feueralarm!",
                "water_alert": "Achtung! Wasserleck!",
                "security_alert": "Achtung! Sicherheitsalarm!",

                "generic_sensor_trigger": "{} wurde ausgelöst.",
                "temperature_sensor_trigger": "{} hat eine kritische Temperatur von {} Grad erreicht.",

                "sensor_info_door_multi": "Folgende Türen wurden geöffnet: {}",
                "sensor_info_window_multi": "Folgende Fenster wurden geöffnet: {}",
                "sensor_info_motion_multi": "Folgende Bewegungsmelder wurden aktiviert: {}",
                "sensor_info_tamper_multi": "Folgende Sensoren wurden manipuliert: {}",
                "sensor_info_environmental_multi": "Folgende Sensoren wurden ausgelöst: {}",

                "sensor_info_door_single": "{} Tür wurde geöffnet",
                "sensor_info_window_single": "{} Fenster wurde geöffnet",
                "sensor_info_motion_single": "{} Bewegungsmelder wurde aktiviert",
                "sensor_info_tamper_single": "{} Sensor wurde manipuliert",
                "sensor_info_environmental_single": "{} Sensor wurde ausgelöst",


                "fire_temperature_alert": "Achtung! Feueralarm! Sensor {} hat eine kritische Temperatur von {} Grad erreicht.",
                "system_start": "Home Assistant System gestartet.",
                "button_disarm": "Achtung, Schalter {} gedrückt. Alarmanlage wird ausgeschaltet.",
                "button_arm_home": "Achtung, Schalter {} gedrückt. Alarmanlage im Modus 'Zuhause' wird aktiviert.",
                "button_arm_away": "Achtung, Schalter {} gedrückt. Alarmanlage im Modus 'Abwesend' wird aktiviert.",
                "auto_arm_night_schedule": "Achtung: Alarmanlage im Modus 'Nacht' wird nach Zeitplan automatisch aktiviert.",
                "auto_arm_night_person": "Achtung: Alarmanlage im Modus 'Nacht' wird automatisch scharf geschaltet. {} hat das Haus betreten.",
                "auto_arm_away_schedule": "Achtung: Alarmanlage im Modus 'Abwesend' wird nach Zeitplan automatisch aktiviert.",
                "auto_arm_away_person": "Achtung: Alarmanlage im Modus 'Abwesend' wird automatisch scharf geschaltet. {} hat das Haus verlassen.",
                "auto_arm_vacation_schedule": "Achtung: Alarmanlage im Modus 'Urlaub' wird nach Zeitplan automatisch aktiviert.",
                "auto_arm_vacation_person": "Achtung: Alarmanlage im Modus 'Urlaub' wird automatisch scharf geschaltet. {} hat das Haus verlassen.",
                "auto_disarm_person": "Achtung: Alarmanlage wird automatisch ausgeschaltet. {} hat das Haus betreten.",
                "auto_disarm_schedule": "Achtung: Alarmanlage wird nach Zeitplan automatisch ausgeschaltet.",
                "alarm_system_state": "Achtung: Der Status der Alarmanlage wurde von {} zu {} geändert.",
                "alarm_system_arming": "Achtung: Die Alarmanlage wird scharf geschaltet.",
                "alarm_system_pending": "Achtung: Die Alarmanlage wird ausgelöst.",
                "alarm_system_triggered": "Achtung: Die Alarmanlage wurde ausgelöst.",
                "alarm_system_armed": "Achtung: Die Alarmanlage ist scharf geschaltet.",
                "alarm_system_disarmed": "Achtung: Die Alarmanlage ist ausgeschaltet.",
                "alarm_system_armed_home": "Achtung: Die Alarmanlage im Modus 'Zuhause' ist scharf geschaltet.",
                "alarm_system_armed_away": "Achtung: Die Alarmanlage im Modus 'Abwesend' ist scharf geschaltet.",
                "alarm_system_armed_night": "Achtung: Die Alarmanlage im Modus 'Nacht' ist scharf geschaltet.",
                "alarm_system_armed_vacation": "Achtung: Die Alarmanlage im Modus 'Urlaub' ist scharf geschaltet."
            },
            "english" : {
                "burglar_alert": "Attention burglar alarm!",
                "fire_alert": "Attention fire alarm!",
                "water_alert": "Attention water leak!",
                "security_alert": "Attention security alarm!",

                "sensor_info_door_multi": "The following doors were opened: {}",
                "sensor_info_window_multi": "The following windows were opened: {}",
                "sensor_info_motion_multi": "The following motion detectors were activated: {}",
                "sensor_info_tamper_multi": "The following sensors were tampered with: {}",
                "sensor_info_environmental_multi": "The following sensors were activated: {}",


                "sensor_info_door_single": "{} door was opened",
                "sensor_info_window_single": "{} window was opened",
                "sensor_info_motion_single": "{} motion detector was activated",
                "sensor_info_tamper_single": "{} sensor was tampered with",
                "sensor_info_environmental_signle": "{} sensor was activated",


                "system_start": "Homeassistant System started",
                "button_disarm": "Attention, switch {} pressed, alarm system will be deactived",
                "button_arm_home": "Attention, switch {} pressed, alarm system will be activated in mode home",
                "button_arm_away": "Attention, switch {} pressed, alarm system will be activated in mode away",
                "auto_arm_night_schedule": "Attention alarm system in night mode will be automatically armed according to schedule",
                "auto_arm_night_person": "Attention alarm system in night mode will be automatically armed, {} has entered the house",
                "auto_arm_away_schedule": "Attention alarm system in away mode will be automatically armed",
                "auto_arm_away_person": "Attention alarm system in away mode will be automatically armed, {} has left the house",
                "auto_arm_vacation_schedule": "Attention alarm system in vacation mode will be automatically armed",
                "auto_arm_vacation_person": "Attention alarm system in vacation mode will be automatically armed, {} has left the house",
                "auto_disarm_person": "Attention alarm system will be automatically disarmed, {} has entered the house",
                "auto_disarm_schedule": "Attention alarm system will be automatically disarmed according to schedule",
                "alarm_system_state": "Attention Alarm system state was changed from {} to {}",
                "alarm_system_arming": "Attention: Alarm system is beeing armed.",
                "alarm_system_pending": "Achtung: Die Alarmanlage is beeing triggered.",
                "alarm_system_triggered": "Attention Alarm system was triggered",
                "alarm_system_armed": "Attention Alarm system is armed",
                "alarm_system_disarmed": "Attention Alarm system is disarmed",
                "alarm_system_armed_home": "Attention Alarm system in home mode is armed",
                "alarm_system_armed_away": "Attention Alarm system in away mode is armed",
                "alarm_system_armed_night": "Attention Alarm system in night mode is armed",
                "alarm_system_armed_vacation": "Attention Alarm system in vacation mode is armed"
            }
        }


        # Setup sane defaults
        self._sensors = {
            'armed_home': {},
            'armed_away': {},
            'armed_night': {},
            'armed_vacation': {},
            'disarmed': {},
            'always': {},
        }

        # Your initial sensor mapping
        self._sensor_mapping: dict = {
            'door': ['door', 'garage_door', 'opening'],
            'window': ['window'],
            'motion': ['motion', 'moving', 'occupancy', 'presence'],
            'tamper': ['tamper', 'sound', 'vibration'],
            'environmental': ['carbon_monoxide', 'gas', 'heat', 'moisture', 'smoke', 'safety', 'temperature']
        }

        # Your initial alarm mapping
        self._alarm_mapping: dict = {
            'burglar': ['door', 'garage_door', 'opening', 'window', 'motion', 'moving', 'occupancy', 'presence', 'tamper', 'sound', 'vibration'],
            'fire': ['carbon_monoxide', 'gas', 'heat', 'smoke', 'temperature'],
            'water': ['moisture'],
            'safety': ['safety']
        }

        # TODO
        # volatile_organic_compounds
        # carbon_dioxide
        # measurement - aqi


        # Achtung Gesundheitsgefahr Folgende Sensoren haben, a, b, c ausgelöst
        # Achtung Einbruchsalarm Folgende Sensoren haben: a, b, c ausgelöst

        # Assign sensor values

        self._sensors['armed_home']['group1'] = self.args.get("armed_home_binary_sensors", [])
        self._sensors['armed_home']['group2'] = self.args.get("armed_home_image_processing_sensors", [])
        self._sensors['armed_away']['group1'] = self.args.get("armed_away_binary_sensors", [])
        self._sensors['armed_away']['group2'] = self.args.get("armed_away_image_processing_sensors", [])
        self._sensors['armed_night']['group1'] = self.args.get("armed_home_binary_sensors", [])
        self._sensors['armed_night']['group2'] = self.args.get("armed_home_image_processing_sensors", [])
        self._sensors['armed_vacation']['group1'] = self.args.get("armed_away_binary_sensors", [])
        self._sensors['armed_vacation']['group2'] = self.args.get("armed_away_image_processing_sensors", [])
        self._sensors['always']['water'] = self.args.get("water_binary_sensors", [])
        self._sensors['always']['smoke'] = self.args.get("fire_binary_sensors", [])
        self._sensors['always']['fire'] = self.args.get("fire_temperature_sensors", [])

        self._sensors_ignored = []

        # arming_state, group_name

        # Thresholds and delays
        self._fire_temperature_threshold = self.args.get("fire_temperature_threshold", 50)
        self._fire_sensor_threshold = 1
        self._water_sensor_threshold = 1
        self._armed_home_sensor_delay = 0
        self._armed_home_sensor_threshold = 1
        self._armed_away_sensor_delay = 10
        self._armed_away_sensor_threshold = 2

        self._sensor_listeners = {}

        # Iterate over sensors and set up listeners
        for arming_state, sensor_dict in self._sensors.items():
            self.log(f"Setting up listeners for state {arming_state}", level="DEBUG")
            for group_name, sensor_list in sensor_dict.items():  # Get group name and sensor list
                self.log(f"Setting up listeners for group {group_name}", level="DEBUG")
                for sensor in sensor_list:  # Iterate over individual sensors
                    sensor_type = self.get_state(sensor, attribute = "device_class")
                    self.log(f"[{sensor}] Setting up listener with type {sensor_type}", level="INFO")
                    if sensor in self._sensor_listeners:
                        self.log(f"[{sensor}] Skipping sensor because we are already listening to it", level="INFO")
                        continue
                    self._sensor_listeners[sensor] = self.listen_state(self.sensor_change_callback, sensor)
                    self._sensor_listeners[sensor + '_delayed'] = self.listen_state(self.sensor_change_callback, sensor, duration=self._armed_away_sensor_delay)

        # controls
        self._alarm_control_buttons = self.args.get("alarm_control_buttons", [])
        self._alarm_lights = self.args.get("alarm_lights", [])
        self._alarm_pin = self.args.get("alarm_pin", None)
        self._arming_state = self.get_alarm_state()

        # sirens
        self._fire_siren_switches = self.args.get("fire_siren_switches", [])
        self._burglar_siren_switches = self.args.get("burglar_siren_switches", [])

        # auto arm time (utc)
        self._alarm_arm_night_after_time = self.args.get("alarm_arm_night_after_time", "23:15:00")
        self._alarm_arm_night_before_time = self.args.get("alarm_arm_night_before_time", "06:00:00")

        # log current config
        self.log(f"Got alarm buttons {self._alarm_control_buttons}")
        self.log(f"Got fire siren switches {self._fire_siren_switches}")
        self.log(f"Got burglar siren switches {self._burglar_siren_switches}")
        self.log(f"Got alarm state {self.get_alarm_state()}")
        self.log(f"Got silent mode {self.in_silent_mode()}")

        self.listen_state(self.control_change_callback, self._alarm_control_panel)

        for button in self._alarm_control_buttons:
            self.listen_event(self.alarm_button_callback, entity_id=button, event_type="state_changed", event="state_changed")

        # auto arm and disarm
        i = 0
        for sensor in self._device_trackers:
            self.listen_state(self.presence_change_callback,
                                sensor, old="home", duration=5 * 60 + i)
            self.listen_state(self.presence_change_callback,
                                sensor, new="home", duration=i)
            self.listen_state(self.presence_change_callback,
                                sensor, new="home", duration=5 * 60 + i)
            i += 1

        if self._vacation_control:
            self.listen_state(self.presence_change_callback, self._vacation_control)

        if self._guest_control:
            self.listen_state(self.presence_change_callback, self._guest_control)

        self._flash_warning_handle = None
        self._media_warning_handle = None

        self._flash_count = 0
        self._media_warning_count = 0
        self._media_warning_max_count = 30
        self._media_warning_inital_delay = 10
        self._media_warning_delay = 5

        self._last_disarm_timestamp = None

        # Alarm type
        self._alarm_type = None
        self._alarm_message = None

        # Init system
        self.stop_burglar_siren()
        self.stop_fire_siren()

        if(self._alarm_arm_night_after_time is not None):
            runtime = self.parse_time(self._alarm_arm_night_after_time)
            self.run_daily(self.perodic_time_callback, runtime)
            self.log(f"Got alarm_arm_night_after_time {runtime}")
        if(self._alarm_arm_night_before_time is not None):
            runtime = self.parse_time(self._alarm_arm_night_before_time)
            self.run_daily(self.perodic_time_callback, runtime)
            self.log(f"Got alarm_arm_night_before_time {runtime}")

        self.log(f"Current alarm_state is {self.get_alarm_state()}")

        self.notify(self.translate("system_start"), prio=1)
        self.notify_awtrix(self.translate("system_start"), "hass_alarm_system_state", 30, 60 * 5)

        # Set start time to now, aligning to the next full 10-minute mark
        self.run_every(self.perodic_time_callback, "now+10", 60*10)

    def terminate(self):
        self.stop_burglar_siren()
        self.stop_fire_siren()
        if not self.is_alarm_disarmed():
            self.disarm_alarm()

    def is_time_in_arm_night_window(self):
        return self.now_is_between(self._alarm_arm_night_after_time, self._alarm_arm_night_before_time)


    def set_alarm_light_color(self, color_name="green", brightness_pct=100):
        self.log(f"Setting alarm light to color {color_name} and brightnes {brightness_pct}")
        for light in self._alarm_lights:
            self.call_service(
                "light/turn_on", entity_id=light, color_name=color_name, brightness_pct=brightness_pct)

    def set_alarm_type(self, alarm_type):
        self.log(f"Setting alarm type to {alarm_type}", level = "DEBUG")
        self._alarm_type = alarm_type

    def get_alarm_type(self):
        return self._alarm_type

    def set_alarm_message(self, message):
        self.log(f"Setting up alarm message: {message}", level = "DEBUG")
        self.notify_awtrix(message, "hass_alarm_msg")
        self._alarm_message = message

    def reset_alarm_message(self):
        self.log("Resetting alarm message", level = "DEBUG")
        self.reset_awtrix("hass_alarm_msg")
        self._alarm_message = None

    def get_alarm_message(self):
        return self._alarm_message

    def flash_warning(self, kwargs):
        for light in self._alarm_lights:
            self.toggle(light)
        self._flash_count += 1
        self.log(f"Flash warning count {self._flash_count}")
        if self._flash_count < 60:
            self._flash_warning_handle = self.run_in(self.flash_warning, 1)

    def start_flash_warning(self, color_name="red", brightness_pct=100):
        if len(self._alarm_lights) == 0:
            self.log("Cannot start flash warning because no alarm lights are defined")
            return
        self.stop_flash_warning()
        self._flash_count = 0
        self.set_alarm_light_color(color_name, brightness_pct)
        self.log(f"Starting flash warning timer with color {color_name} and brightnes {brightness_pct}")
        self._flash_warning_handle = self.run_in(self.flash_warning, 1)

    def stop_flash_warning(self):
        if len(self._alarm_lights) == 0:
            self.log("Cannot stop flash warning because no alarm lights are defined")
            return
        if self._flash_warning_handle is not None:
            self.log("Stopping flash warning timer")
            self.cancel_timer(self._flash_warning_handle)
            self._flash_count = 60
            self._flash_warning_handle = None

    def media_warning(self, kwargs):
        self.media_warning_with_delay(self.get_alarm_message())
        self._media_count += 1
        self.log(f"Media warning count {self._media_count}")
        if self._media_count < self._media_warning_max_count:
            self._media_warning_handle = self.run_in(self.media_warning, self._media_warning_delay + 5)

    def media_warning_with_delay(self, message, delay=5):
        """Send each message with a delay"""
        self.run_in(self.notify_media, delay, message=message)

    def start_media_warning(self):
        self.stop_media_warning()
        self._media_count = 0
        self.log("Starting media warning timer")
        self._media_warning_handle = self.run_in(self.media_warning, self._media_warning_inital_delay)

    def stop_media_warning(self):
        if self._media_warning_handle is not None:
            self.log("Stopping media warning timer")
            self.cancel_timer(self._media_warning_handle)
            self._media_count = self._media_warning_max_count
            self._media_warning_handle = None

    def start_burglar_siren(self):
        if self.in_silent_mode():
            self.log("Suppressed siren because of silent mode")
            return

        for siren in self._burglar_siren_switches:
            self.log(f"Turning on burglar siren {siren}")
            self.turn_on(siren)

    def stop_burglar_siren(self):
        for siren in self._burglar_siren_switches:
            self.log(f"Turning off burglar siren {siren}")
            self.turn_off(siren)

    def start_fire_siren(self):
        for siren in self._fire_siren_switches:
            self.log(f"Turning on fire siren {siren}")
            self.turn_on(siren)

    def stop_fire_siren(self):
        for siren in self._fire_siren_switches:
            self.log(f"Turning off fire siren {siren}")
            self.turn_off(siren)

    def debug_event(self, event_name, data, kwargs):
        self.log(f"Debug event {event_name}:{data} {kwargs}")

    def alarm_button_callback(self, event_name, data, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {event_name}:{data}")

        event_type = data['new_state']['attributes'].get('event_type', None)
        if event_type is None:
            self.log(f"Warning: 'event_type' not found in {data['new_state']['attributes']}", level="WARNING")
            return  # Exit early to prevent further errors
        entity_id = data['entity_id']

        self.log(f"Got event type {event_type}")

        if event_type == "single":
            self.button_arm_home(entity_id)
        elif event_type == "double":
            self.button_arm_away(entity_id)
        elif event_type == "hold":
            self.button_disarm(entity_id)
        elif event_type == "quadruple":
            self.button_trigger_alarm(entity_id)
        elif event_type == "triple":
            self.button_trigger_alarm(entity_id)
        else:
            self.log("Ignoring event")

    def button_arm_away(self, entity):
        if(self.is_alarm_disarmed() == False):
            self.log(f"Ignoring call because alarm system is in state {self.get_alarm_state()}")
            return

        mode = "arm_away"
        if(self.in_vacation_mode()):
            mode = "arm_vacation"

        message = self.translate("button_{}".format(mode)).format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)

        self.arm_alarm('away')

    def button_arm_home(self, entity):
        if(self.is_alarm_disarmed() == False):
            self.log(f"Ignoring call because alarm system is in state {self.get_alarm_state()}")
            return

        message = self.translate("button_arm_home").format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)

        self.arm_alarm('home')

    def button_disarm(self, entity):
        if(self.is_alarm_disarmed()):
            self.log(f"Ignoring call because alarm system is in state {self.get_alarm_state()}")
            return

        message = self.translate("button_disarm").format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)

        self.disarm_alarm()

    def button_trigger_alarm(self, entity):
        self.log("Trigger alarm using button")

        if self.get_state("binary_sensor.zigbee2mqtt_bridge_connection_state") != 'on':
            self.log("Doing nothing because zigbee2mqtt_bridge_connection_state is not on")
            return
        if self.get_seconds_since_update("binary_sensor.zigbee2mqtt_bridge_connection_state") < 300:
            self.log("Doing nothing because zigbee2mqtt_bridge_connection_state is not online more than 300 seconds")
            return

        message = self.translate("security_alert").format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)
        #self.add_alarm_message(message)

        self.trigger_alarm('security')

    def classify_sensor(self, device_class: str) -> str:
        matched_types = []

        for sensor_type, keywords in self._sensor_mapping.items():
            if device_class in keywords:
                return sensor_type
        return None

    def classify_alarm(self, device_class: str) -> str:
        matched_types = []

        for sensor_type, keywords in self._alarm_mapping.items():
            if device_class in keywords:
                return sensor_type
        return None

    def is_sensor_monitored(self, sensor):
        desired_arming_states = ['always', self.get_alarm_state(), self._arming_state]

        if sensor in self._sensors_ignored:
            return False

        for arming_state, groups in self._sensors.items():
            if arming_state not in desired_arming_states:
                continue
            for group, sensors in groups.items():
                if sensor in sensors:
                    return True
        return False

    def check_sensor(self, sensor, desired_state = 'off', timeout = None):
        sensor_type = self.get_state(sensor, attribute = "device_class")
        sensor_state = self.get_state(sensor)
        last_update = self.get_seconds_since_update(sensor)
        sensor_classification = self.classify_sensor(sensor)

        if timeout is None:
            if sensor_classification == 'motion':
                timeout = self._motion_timeout
            elif sensor_classification in ['door', 'window']:
                timeout = self._opening_timeout

        # FIXME only count sensors if they are on for some time?

        if sensor_state in [None, "unknown", "unavailable"]:
            self.log(f"[{sensor}] Warning: Sensor is in an invalid state {sensor_state}", level="WARNING")
            return True

        if sensor_type == 'temperature':
            if float(sensor_state) > self._fire_temperature_threshold:
                self.log(f"[{sensor}] Warning: Sensor temperature ({sensor_state}°C) exceeds the threshold of {self._fire_temperature_threshold}°C.", level="WARNING")
                return False
            else:
                self.log(f"[{sensor}] OK: Sensor temperature ({sensor_state}°C) is within the normal range.", level="INFO")
                return True

        if sensor_state != desired_state:
            self.log(f"[{sensor}] Warning: Sensor is in an unexpected state ('{sensor_state}'), expected: '{desired_state}'.", level="WARNING")
            return False

        if timeout is not None and last_update is not None:
            if last_update < timeout:
                self.log(f"[{sensor}] Warning: Sensor is in state '{sensor_state}', but it changed {last_update:.2f} seconds ago, which is within the timeout period.", level="WARNING")
                return False

        self.log(f"[{sensor}] OK: Sensor is in the desired state ('{sensor_state}').", level="INFO")

        return True


    def get_alerts(self, timeout = None, arming_state = None):
        alerts = {}

        if arming_state is None:
            arming_state = self.get_alarm_state()

        desired_arming_states = ['always', arming_state]
        desired_sensor_state = 'on'

        self.log(f"Looking for sensors in category {desired_arming_states}")

        # Iterate over sensors and set up listeners
        for arming_state, sensor_dict in self._sensors.items():

            if arming_state not in desired_arming_states:
                self.log(f"Ignoring category {arming_state}")
                continue

            self.log(f"Checking category {arming_state}")
            for group_name, sensor_list in sensor_dict.items():  # Get group name and sensor list

                self.log(f"Checking group {group_name} in category {arming_state}")
                for sensor in sensor_list:  # Iterate over individual sensors
                    sensor_type = self.get_state(sensor, attribute = "device_class")
                    sensor_state = self.get_state(sensor)
                    self.log(f"[{sensor}] Got {sensor_type} {sensor_state}", level="DEBUG")

                    alarm_category = self.classify_alarm(sensor_type)

                    if sensor in self._sensors_ignored:
                        self.log(f"[{sensor}] Skipping {sensor_type} sensor because it is in ignore list")
                        continue

                    if alarm_category is None:
                        self.log(f"[{sensor}] Skipping {sensor_type} sensor because it is not a valid device class")
                        continue

                    if sensor_state in [None, "unknown", "unavailable"]:
                        self.log(f"[{sensor}] Skipping {sensor_type} sensor because the state is invalid ({sensor_state})")
                        continue  # Skip invalid states

                    if not self.check_sensor(sensor, 'off', timeout):
                        if alarm_category not in alerts:
                            alerts[alarm_category] = []  # Initialize as an empty list
                        if sensor not in alerts[alarm_category]:
                            alerts[alarm_category].append(sensor)

        return alerts

    def ignore_sensors(self, arming_state):
        alerts = self.get_alerts(0, arming_state)
        self._sensors_ignored = []

        for alarm_type, sensor_list in alerts.items():
            for sensor in sensor_list:
                if sensor not in self._sensors_ignored:
                    self.log(f"[{sensor}] adding sensor to ignore list")
                    self._sensors_ignored.append(sensor)

    def count_alerts_by_arming_state(self, arming_state, timeout = None):
        alerts = self.get_alerts(timeout, arming_state)

        # Count items in each category
        category_counts = {category: len(items) for category, items in alerts.items()}
        self.log(f"Found these alerts: {alerts}")
        total_count = sum(category_counts.values())

        return total_count

    def is_arming_home_possible(self):
        if self.count_alerts_by_arming_state('armed_home', 30) > 0:
            return False
        return True

    def is_arming_away_possible(self):
        if self.count_alerts_by_arming_state('armed_away', 30) > 0:
            return False
        return True

    def is_auto_arming_home_allowed(self):
        return False

    def is_auto_arming_away_allowed(self):
        return True

    def is_auto_arming_night_allowed(self):
        return True

    def is_auto_arming_vacation_allowed(self):
        return True

    def is_last_disarming_recent(self):
        if self._last_disarm_timestamp is None:
            return False

        # Get current time in UTC
        now = datetime.now(timezone.utc)

        # Calculate seconds since the last external change
        last_change = self._last_disarm_timestamp
        seconds_ago = (now - last_change).total_seconds()

        if seconds_ago < 600:
            return True
        return False

    def is_auto_arming_allowed(self):
        if self.is_last_disarming_recent():
            return False
        if self.in_guest_mode():
            return False
        if self.in_vacation_mode():
            return self.is_auto_arming_vacation_allowed()
        if self.is_somebody_at_home():
            if self.is_time_in_arm_night_window():
                return self.is_auto_arming_night_allowed()
            return self.is_auto_arming_home_allowed()
        if self.is_nobody_at_home():
            return self.is_nobody_at_home()

    def get_desired_arming_state(self):
        if self.in_vacation_mode():
            return 'vacation'
        if self.is_somebody_at_home():
            if self.is_time_in_arm_night_window():
                return 'night'
            return self.is_auto_arming_home_allowed()
        if self.is_nobody_at_home():
            return 'away'
        if self.is_somebody_at_home():
            return 'home'
        return None

    def setup(self):
        if self.is_alarm_pending():
            self.log("Doing nothing because alarm is already pending")
            return
        if self.is_alarm_arming():
            self.log("Doing nothing because alarm is already arming")
            return
        if self.is_alarm_triggered():
            self.log("Doing nothing because alarm is already triggered")
            return
        if self.is_alarm_disarmed() and not self.is_auto_arming_allowed():
            self.log("Doing nothing because alarm is disarmed and arming is not allowed")
            return

        self.log(f"There are {self.count_home_device_trackers()} device_trackers home and {self.count_not_home_device_trackers()} device_trackers not home")
        self.log(f"Guest mode is set to {self.in_guest_mode()}")
        self.log(f"Vacation mode mode is set to {self.in_vacation_mode()}")

        if self.is_nobody_at_home():
            if self.in_vacation_mode():
                if self.is_alarm_armed_vacation():
                    self.log("Doing nothing because alarm is already armed vacation")
                    return
                if self.is_auto_arming_allowed():
                    self.arm_alarm('vacation')
                    return

            if self.is_alarm_armed_away():
                self.log("Doing nothing because alarm is already armed away")
                return
            if self.is_auto_arming_allowed():
                self.arm_alarm('away')
                return
            return

        if self.is_somebody_at_home():
            if self.is_time_in_arm_night_window():
                if not self.is_auto_arming_allowed():
                    self.log("Doing nothing because arming is not allowed right now")
                    return
                if self.is_alarm_armed_night():
                    self.log("Doing nothing because alarm is already armed night")
                    return

                if self.is_auto_arming_allowed():
                    self.arm_alarm('night')
                    return

            if self.is_alarm_armed_home():
                self.log("Doing nothing because alarm is already armed home")
                return

            self.disarm_alarm()
            return


    def analyze_and_trigger(self):

        if self.get_state("binary_sensor.zigbee2mqtt_bridge_connection_state") != 'on':
            self.log("Doing nothing because zigbee2mqtt_bridge_connection_state is not on")
            return
        if self.get_seconds_since_update("binary_sensor.zigbee2mqtt_bridge_connection_state") < 300:
            self.log("Doing nothing because zigbee2mqtt_bridge_connection_state is not online more than 300 seconds")
            return

        self.log(f"There are {self.count_home_device_trackers()} device_trackers home and {self.count_not_home_device_trackers()} device_trackers not home")
        self.log(f"Guest mode is set to {self.in_guest_mode()}")
        self.log(f"Vacation mode mode is set to {self.in_vacation_mode()}")

        if self.is_alarm_pending():
            self.log("Doing nothing because alarm is already pending")
            return

        if self.is_alarm_arming():
            self.log("Doing nothing because alarm is arming")
            return

        if self.is_alarm_triggered():
            alerts = self.get_alerts(None, self._arming_state)
            self.log("Updating alarm message")
            self.set_alarm_message(self.create_alarm_message(alerts))
            self.log("Doing nothing because alarm is already triggered")
            return

        self.log(f"Fetching current alerts")
        alerts = self.get_alerts()

        if sum(len(v) for v in alerts.values()) == 0:
            self.log("Doing nothing because there are no alerts")
            return

        self.log(f"Analyzing these alerts: {alerts}")

        self.log(f"Checking fire alerts, found {len(alerts.get('fire', []))}, threshold {self._fire_sensor_threshold}")
        if len(alerts.get('fire', [])) > 0:
            self.trigger_alarm('fire', alerts)
            return

        self.log(f"Checking water alerts, found {len(alerts.get('water', []))}, threshold {self._water_sensor_threshold}")
        if len(alerts.get('water', [])) > 0:
            self.trigger_alarm('water', alerts)
            return

        if self.is_alarm_armed_away() or self.is_alarm_armed_vacation():
            self.log(f"Checking burglar alerts, found {len(alerts.get('burglar', []))}, threshold {self._armed_away_sensor_threshold}")
            if len(alerts.get('burglar', [])) >= self._armed_away_sensor_threshold:
                self.trigger_alarm('burglar', alerts)
                return

        if self.is_alarm_armed_home() or self.is_alarm_armed_night():
            self.log(f"Checking burglar alerts, found {len(alerts.get('burglar', []))}, threshold {self._armed_home_sensor_threshold}")
            if len(alerts.get('burglar', [])) >= self._armed_home_sensor_threshold:
                self.trigger_alarm('burglar', alerts)
                return

    def optimize_sensor_name(self, sensor):
        name = self.get_state(sensor, attribute = "friendly_name")
        name = name.replace("/", " ")
        name = name.replace("/", " ")
        name = name.replace("_", " ")
        name = re.sub(r"(?i)bewegungsmelder", "", name)
        name = re.sub(r"(?i)fenstersensor", "", name)
        name = re.sub(r"(?i)türsensor", "", name)
        name = re.sub(r"(?i)rauchmelder", "", name)
        name = re.sub(r"(?i)sensor", "", name)
        name = re.sub(r"(?i)manipulation", "", name)
        name = re.sub(r"(?i)radar", "", name)
        name = name.strip()
        return name

    def create_alarm_message(self, alerts):
        messages = []
        sensors_by_category = {}

        self.log(f"Creating alarm message based on this alerts: {alerts}")

        for alarm_type, sensor_list in alerts.items():
            self.log(f"Alarm Type: {alarm_type}")
            translation_key = alarm_type + '_alert'
            messages.append(self.translate(translation_key))
            devices = []
            for sensor in sensor_list:
                name = self.optimize_sensor_name(sensor)
                sensor_type = self.get_state(sensor, attribute = "device_class")
                sensor_category = self.classify_sensor(sensor_type)
                if sensors_by_category.get(sensor_category) is None:
                    sensors_by_category[sensor_category] = []
                if name not in sensors_by_category[sensor_category]:
                    sensors_by_category[sensor_category].append(name)

        for sensor_category, sensor_list in sensors_by_category.items():
            translation_key = 'sensor_info_' + sensor_category + '_single'
            sensor_name = ", ".join(sensor_list)
            if len(sensor_list) > 1:
                translation_key = 'sensor_info_' + sensor_category + '_multi'

            sentence = self.translate(translation_key).format(sensor_name)
            message = sentence[0].upper() + sentence[1:] + '.'
            messages.append(message)

        message = " ".join(messages)

        self.log(f"Created alarm message: {message}")

        return (message)

    def call_alarm_control_panel(self, service_action):
        self.log("Calling service alarm_control_panel/" + service_action)
        self.call_service("alarm_control_panel/" + service_action,
                            entity_id=self._alarm_control_panel, code=self._alarm_pin)

    def arm_alarm(self, mode):
        self.log("arm_alarm_" + mode, level="WARNING")
        service_action = 'alarm_arm_' + mode
        self.call_alarm_control_panel(service_action)

    def disarm_alarm(self):
        self.log("disarm_alarm", level="WARNING")
        self.call_alarm_control_panel('alarm_disarm')

    def trigger_alarm(self, alarm_type, alerts = {}):
        self.log("trigger_alarm_" + alarm_type, level="WARNING")

        self.set_alarm_type(alarm_type)
        self.set_alarm_message(self.create_alarm_message(alerts))
        #self.notify(message)
        #self.add_alarm_message(message)
        self.call_alarm_control_panel("alarm_trigger")

    def perodic_time_callback(self, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name}")

        self.setup()
        self.analyze_and_trigger()

    def presence_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        if entity in self._device_trackers and new == 'home':
            if self.is_alarm_armed() or self.is_alarm_pending() or self.is_alarm_triggered():
                self.disarm_alarm()
                return

        self.setup()

    def sensor_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        if self.is_sensor_monitored(entity):
            self.analyze_and_trigger()

    def control_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {entity}:{attribute} {old}->{new}")

        message = self.translate("alarm_system_" + self.get_alarm_state())
        message_prio = 1

        if self.is_alarm_triggered():
            self.start_flash_warning('red')
            self.start_media_warning()
            if self.get_alarm_type() == 'burglar':
                self.start_burglar_siren()
            if self.get_alarm_type() == 'fire':
                self.start_fire_siren()
            message = message + " " + self.get_alarm_message()
            message_prio = 0

        if self.is_alarm_pending():
            self.start_flash_warning('orange')
            message = message + " " + self.get_alarm_message()

        if self.is_alarm_arming():
            if not self.is_time_in_night_window():
                self.start_flash_warning('yellow', 50)

        if self.is_alarm_armed():
            self.reset_alarm_message()
            self._arming_state = self.get_alarm_state()
            if self.count_alerts_by_arming_state(self._arming_state) > 0:
                self.log(f"There are still {self.count_alerts_by_arming_state(self._arming_state)} sensors active, we are going to ignore them", level="WARNING")
                self.ignore_sensors(self._arming_state)

        if self.is_alarm_disarmed():
            self.reset_alarm_message()
            self._last_disarm_timestamp = datetime.now(timezone.utc)
            self._sensors_ignored = []
            self.set_alarm_light_color('green', 10)

        if self.is_alarm_disarmed() or self.is_alarm_armed():
            self.stop_fire_siren()
            self.stop_burglar_siren()
            self.stop_media_warning()
            self.stop_flash_warning()
            self.set_alarm_type(None)

        self.notify(message, prio=message_prio)
        self.notify_awtrix(message, "hass_alarm_system_state", 60, 60 * 60 * 1)
