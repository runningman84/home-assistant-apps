import appdaemon.plugins.hass.hassapi as hass
import datetime
import time
import re

#
# AlarmSystem App
#
# Args:
#


class AlarmSystem(hass.Hass):

    def initialize(self):
        self.log("Hello from AlarmSystem")

        # setup sane defaults
        # sensors
        # burglar
        self.__armed_home_binary_sensors = self.args.get("armed_home_binary_sensors", [])
        self.__armed_home_image_processing_sensors = self.args.get("armed_home_image_processing_sensors", [])
        self.__armed_away_binary_sensors = self.args.get("armed_away_binary_sensors", [])
        self.__armed_away_image_processing_sensors = self.args.get("armed_away_image_processing_sensors", [])
        # water
        self.__water_binary_sensors = self.args.get("water_binary_sensors", [])
        # fire
        self.__fire_binary_sensors = self.args.get("fire_binary_sensors", [])
        self.__fire_temperature_sensors = self.args.get("fire_temperature_sensors", [])
        self.__fire_temperature_threshold = self.args.get("fire_temperature_threshold", 50)
        self.__device_trackers = self.args.get("device_trackers", [])
        # controls
        self.__vacation_control = self.args.get("vacation_control", None)
        self.__guest_control = self.args.get("guest_control", None)
        self.__alarm_control_panel = self.args.get(
            "alarm_control_panel", "alarm_control_panel.ha_alarm")
        self.__alarm_control_buttons = self.args.get("alarm_control_buttons", [])
        self.__alarm_lights = self.args.get("alarm_lights", [])
        self.__alarm_pin = self.args.get("alarm_pin", None)
        self.__alarm_volume_control = self.args.get(
            "alarm_volume_control", None)
        self.__info_volume_control = self.args.get("info_volume_control", None)
        self.__silent_control = self.args.get("silent_control", None)
        # notifications
        self.__notify_service = self.args.get("notify_service", None)
        self.__notify_title = self.args.get(
            "notify_title", "AlarmSystem triggered, possible {}")
        self.__telegram_user_ids = self.args.get("telegram_user_ids",[])
        self.__alexa_media_devices = self.args.get("alexa_media_devices",[])
        self.__alexa_monkeys = self.args.get("alexa_monkeys",[])
        self.__tts_devices = self.args.get("tts_devices",[])
        # cameras
        self.__cameras = self.args.get("cameras", [])
        self.__camera_folder_watcher = self.args.get("camera_folder_watcher", False)
        self.__camera_snapshot_path = self.args.get("camera_snapshot_path", '/tmp')
        self.__camera_snapshot_regex = self.args.get("camera_snapshot_regex", "camera_.*\\d+_\\d+\\.jpg")
        # sirens
        self.__fire_siren_switches = self.args.get("fire_siren_switches", [])
        self.__burglar_siren_switches = self.args.get("burglar_siren_switches", [])

        # auto arm time (utc)
        self.__alarm_arm_night_after_time = self.args.get("alarm_arm_night_after_time", "23:15:00")
        self.__alarm_arm_night_before_time = self.args.get("alarm_arm_night_before_time", "06:00:00")
        # sleep time
        self.__sleep_after_time = self.args.get("sleep_after_time", "22:00:00")
        self.__sleep_before_time = self.args.get("sleep_before_time", "07:00:00")

        # translation
        self.__language = self.args.get("language","english")
        self.__translation = {
            "german" : {
                "burglar_alert": "Achtung! Einbruchsalarm! Sensor {} wurde ausgelöst",
                "fire_alert": "Achtung! Feueralarm! Sensor {} wurde ausglöst",
                "fire_temperature_alert": "Achtung! Feueralarm! Sensor {} hat eine kritische Temperatur von {} Grad erreicht",
                "water_leak_alert": "Achtung! Wasserleck! Sensor {} wurde ausgelöst",
                "system_start": "Homeassistant System gestartet",
                "button_disarm": "Achtung, Schalter {} gedrückt, Alarmanlage wird ausgeschaltet",
                "button_arm_home": "Achtung, Schalter {} gedrückt, Alarmanlage im Modus Zuhause wird aktiviert",
                "button_arm_away": "Achtung, Schalter {} gedrückt, Alarmanlage im Modus Abwsendet wird aktiviert",
                "auto_arm_night_schedule": "Achtung Alarmanlage im Modus Nacht wird nach Zeitplan automatisch aktiviert",
                "auto_arm_night_person": "Achtung Alarmanlage im Modus Nacht wird automatisch scharf geschaltet, {} hat das Haus betreten",
                "auto_arm_away_schedule": "Achtung Alarmanlage im Modus Abwesend wird nach Zeitplan automatisch aktiviert",
                "auto_arm_away_person": "Achtung Alarmanlage im Modus Abwesend wird automatisch scharf geschaltet, {} hat das Haus verlassen",
                "auto_arm_vacation_schedule": "Achtung Alarmanlage im Modus Urlaub wird nach Zeitplan automatisch aktiviert",
                "auto_arm_vacation_person": "Achtung Alarmanlage im Modus Urlaub wird automatisch scharf geschaltet, {} hat das Haus verlassen",
                "auto_disarm_person": "Achtung Alarmanlage wird automatisch ausgeschaltet, {} hat das Haus betreten",
                "auto_disarm_schedule": "Achtung Alarmanlage wird nach Zeitplan automatisch ausgeschaltet",
                "alarm_system_state": "Achtung Alarmanlage Status wurde verändert von {} in {}",
                "alarm_system_triggered": "Achtung Alarmanlage wurde ausgelöst",
                "alarm_system_armed": "Achtung Alarmanlage ist scharf geschaltet",
                "alarm_system_disarmed": "Achtung Alarmanlage ist ausgeschaltet",
                "alarm_system_armed_home": "Achtung Alarmanlage im Modus Zuhause ist scharf geschaltet",
                "alarm_system_armed_away": "Achtung Alarmanlage im Modus Abwesend ist scharf geschaltet",
                "alarm_system_armed_night": "Achtung Alarmanlage im Modus Nacht ist scharf geschaltet",
                "alarm_system_armed_vacation": "Achtung Alarmanlage im Modus Urlaub ist scharf geschaltet"
            },
            "english" : {
                "burglar_alert": "Attention burglar alarm, sensor {} has triggered",
                "fire_alert": "Attention Attention Attention fire alarm, sensor {} has triggered",
                "fire_temperature_alert": "Attention fire alarm, sensor {} has reached a critical temperature of {} degrees",
                "water_leak_alert": "Attention water leak, Sensor {} was triggered",
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
                "alarm_system_triggered": "Attention Alarm system was triggered",
                "alarm_system_armed": "Attention Alarm system is armed",
                "alarm_system_disarmed": "Attention Alarm system is disarmed",
                "alarm_system_armed_home": "Attention Alarm system in home mode is armed",
                "alarm_system_armed_away": "Attention Alarm system in away mode is armed",
                "alarm_system_armed_night": "Attention Alarm system in night mode is armed",
                "alarm_system_armed_vacation": "Attention Alarm system in vacation mode is armed"
            }
        }

        # log current config
        self.log("Got armed_home binary sensors {}".format(
            self.__armed_home_binary_sensors))
        self.log("Got armed_home image processing sensors {}".format(
            self.__armed_home_image_processing_sensors))
        self.log("Got armed_away binary sensors {}".format(
            self.__armed_away_binary_sensors))
        self.log("Got armed_away image processing sensors {}".format(
            self.__armed_away_image_processing_sensors))
        self.log("Got alarm buttons {}".format(self.__alarm_control_buttons))
        self.log("Got fire siren switches {}".format(self.__fire_siren_switches))
        self.log("Got burglar siren switches {}".format(self.__burglar_siren_switches))
        self.log("Got device trackers {}".format(self.__device_trackers))
        self.log("Got {} device_trackers home and {} device_trackers not home".format(
            self.count_home_device_trackers(), self.count_not_home_device_trackers()))
        self.log("Got guest mode {}".format(self.in_guest_mode()))
        self.log("Got vacation mode {}".format(self.in_vacation_mode()))
        self.log("Got silent mode {}".format(self.in_silent_mode()))
        self.log("Got info volume {}".format(self.get_info_volume()))
        self.log("Got alarm volume {}".format(self.get_alarm_volume()))
        self.log("Got notify service {}".format(self.__notify_service))
        self.log("Got alarm state {}".format(self.get_alarm_state()))
        self.log("Got language {}".format(self.__language))
        self.log("Got alexa media devices {}".format(self.__alexa_media_devices))
        self.log("Got alexa voice monkeys {}".format(self.__alexa_monkeys))

        self.listen_state(self.alarm_state_triggered_callback,
                          self.__alarm_control_panel, new="triggered")
        self.listen_state(self.alarm_state_from_armed_home_to_pending_callback,
                          self.__alarm_control_panel, old="armed_home", new="pending")
        self.listen_state(self.alarm_state_from_armed_home_to_pending_callback,
                          self.__alarm_control_panel, old="armed_night", new="pending")
        self.listen_state(self.alarm_state_from_armed_away_to_pending_callback,
                          self.__alarm_control_panel, old="armed_away", new="pending")
        self.listen_state(self.alarm_state_from_armed_away_to_pending_callback,
                          self.__alarm_control_panel, old="armed_vacation", new="pending")
        self.listen_state(self.alarm_state_from_disarmed_to_pending_callback,
                          self.__alarm_control_panel, old="disarmed", new="pending")
        self.listen_state(self.alarm_state_disarmed_callback,
                          self.__alarm_control_panel, new="disarmed")
        self.listen_state(self.alarm_state_armed_away_callback,
                          self.__alarm_control_panel, new="armed_away")
        self.listen_state(self.alarm_state_armed_away_callback,
                          self.__alarm_control_panel, new="armed_vacation")
        self.listen_state(self.alarm_state_armed_home_callback,
                          self.__alarm_control_panel, new="armed_home")
        self.listen_state(self.alarm_state_armed_night_callback,
                          self.__alarm_control_panel, new="armed_night")

        for sensor in self.__alarm_control_buttons:
            #self.listen_event(self.event_test_callback, sensor, )

            #self.listen_state(self.button_arm_home_callback,
            #                  sensor, new="single")
            #self.listen_state(self.button_disarm_callback,
            #                  sensor, new="double")
            #self.listen_state(self.button_arm_away_callback,
            #                  sensor, new="long")

            self.listen_event(self.alarm_button_callback, entity_id=sensor, event_type="state_changed", event="state_changed")




        # auto arm and disarm
        i = 0
        for sensor in self.__device_trackers:
            self.listen_state(self.alarm_arm_away_auto_callback,
                              sensor, old="home", duration=5 * 60 + i)
            self.listen_state(self.alarm_disarm_auto_callback,
                              sensor, new="home", duration=i)
            self.listen_state(self.alarm_arm_night_auto_state_change_callback,
                              sensor, new="home", duration=5 * 60 + i)
            i += 1

        # Images
        if self.__camera_folder_watcher:
            self.listen_event(self.camera_snapshot_stored_callback, 'folder_watcher', event_type="created")

        self.__flash_warning_handle = None
        self.__media_warning_handle = None
        self.__camera_snapshot_handle = None
        self.__flash_count = 0
        self.__media_warning_count = 0
        self.__media_warning_max_count = 30
        self.__media_warning_inital_delay = 10
        self.__media_warning_delay = 5

        self.__snap_count = 0
        self.__sensor_handles = {}

        # Alarm type
        self.__alarm_type = None
        self.__alarm_messages = []

        # Init system
        self.set_alarm_light_color_based_on_state()
        self.stop_burglar_siren()
        self.stop_fire_siren()
        self.start_sensor_listeners()

        if(self.__alarm_arm_night_after_time is not None):
            runtime = self.parse_time(self.__alarm_arm_night_after_time)
            self.run_daily(self.alarm_arm_night_auto_timer_callback, runtime)
            self.log("Got alarm_arm_night_after_time {}".format(runtime))
        if(self.__alarm_arm_night_before_time is not None):
            runtime = self.parse_time(self.__alarm_arm_night_before_time)
            self.run_daily(self.alarm_disarm_night_auto_timer_callback, runtime)
            self.log("Got alarm_arm_night_before_time {}".format(runtime))

        self.log("Current alarm_state is {}".format(self.get_alarm_state()))

        self.notify(self.translate("system_start"), prio=1)

    def start_sensor_listeners(self):
        self.start_fire_binary_sensor_listeners()
        self.start_fire_temperature_sensor_listeners()
        self.start_water_binary_sensor_listeners()
        if self.is_alarm_armed_away():
            self.start_armed_away_binary_sensor_listeners()
        elif self.is_alarm_armed_home():
            self.start_armed_home_binary_sensor_listeners()

    def start_armed_home_binary_sensor_listeners(self):
        for sensor in self.__armed_home_binary_sensors:
            self.__sensor_handles[sensor] = self.listen_state(
                self.trigger_alarm_while_armed_home_callback, sensor, new="on", old="off")
        for sensor in self.__armed_home_image_processing_sensors:
            self.__sensor_handles[sensor] = self.listen_state(
                self.trigger_alarm_while_armed_home_callback, sensor)

    def start_armed_away_binary_sensor_listeners(self):
        for sensor in self.__armed_away_binary_sensors:
            self.__sensor_handles[sensor] = self.listen_state(
                self.trigger_alarm_while_armed_away_callback, sensor, new="on", old="off")
        for sensor in self.__armed_away_image_processing_sensors:
            self.__sensor_handles[sensor] = self.listen_state(
                self.trigger_alarm_while_armed_away_callback, sensor)

    def start_fire_binary_sensor_listeners(self):
        for sensor in self.__fire_binary_sensors:
            self.listen_state(
                self.trigger_alarm_fire_callback, sensor, new="on", old="off")

    def start_fire_temperature_sensor_listeners(self):
        for sensor in self.__fire_temperature_sensors:
            self.listen_state(
                self.trigger_alarm_fire_temperature_callback, sensor)

    def start_water_binary_sensor_listeners(self):
        for sensor in self.__water_binary_sensors:
            self.listen_state(
                self.trigger_alarm_water_callback, sensor, new="on", old="off")

    def stop_sensor_listeners(self):
        for handle in self.__sensor_handles:
            if self.__sensor_handles[handle] is not None:
                self.cancel_listen_state(self.__sensor_handles[handle])
                self.__sensor_handles[handle] = None

    # def count_doors_and_windows(self, state):
    #     count = 0
    #     for sensor in self.__door_window_sensors:
    #         if self.get_state(sensor) == state:
    #             count = count + 1
    #     return count

    # def count_open_doors_and_windows(self):
    #     return self.count_doors_and_windows("on")

    # def count_closed_doors_and_windows(self):
    #     return self.count_doors_and_windows("off")

    def count_device_trackers(self, state):
        count = 0
        for sensor in self.__device_trackers:
            if self.get_state(sensor) == state:
                self.log("Device tracker {} is at {}".format(sensor, state), level = "DEBUG")
                count = count + 1
        return count

    def count_home_device_trackers(self):
        count = 0
        for sensor in self.__device_trackers:
            if self.get_state(sensor) == "home":
                self.log("Device tracker {} is at home".format(sensor), level = "DEBUG")
                count = count + 1
        return count

    def count_not_home_device_trackers(self):
        count = 0
        for sensor in self.__device_trackers:
            if self.get_state(sensor) != "home":
                self.log("Device tracker {} is not at home".format(sensor), level = "DEBUG")
                count = count + 1
        return count

    def in_guest_mode(self):
        if self.__guest_control is None:
            return False
        if self.get_state(self.__guest_control) == 'on':
            return True
        else:
            return False

    def in_vacation_mode(self):
        if self.__vacation_control is None:
            return False
        if self.get_state(self.__vacation_control) == 'on':
            return True
        else:
            return False

    def get_alarm_volume(self):
        if self.__alarm_volume_control is None:
            return 99
        return int(float(self.get_state(self.__alarm_volume_control)))

    def get_info_volume(self):
        if self.__info_volume_control is None:
            return 10
        return int(float(self.get_state(self.__info_volume_control)))

    def notify(self, message, title=None, prio=0):
        # prio
        # 0 = urgent
        # 1 = other
        # 2 = debug
        if self.is_time_in_sleep_window() and prio > 0:
            self.log("Ignoring notify alexa due to sleep time")
        else:
            self.notify_media(message = message, title = title, prio = prio)

        self.notify_telegram(message)
        self.notify_notify(message)

    def notify_telegram(self, message):
        for user_id in self.__telegram_user_ids:
            self.log("Calling service telegram_bot/send_message with user_id {} and message: {}".format(user_id, message))
            self.call_service('telegram_bot/send_message',
                                title='*Alarm System*',
                                target=user_id,
                                message=message,
                                disable_notification=True)

    def notify_notify(self, message):
        self.log("Calling service notify/notify with message: {}".format(message))
        self.call_service('notify/notify',
                            title='*Alarm System*',
                            message=message)

    def notify_media(self, *args, **kwargs):
        # If a scheduled callback passed a dictionary as a positional argument,
        # merge it with any keyword arguments provided.
        if args and isinstance(args[0], dict):
            kwargs = {**args[0], **kwargs}

        # Extract parameters, using 'message' as the key (or fallback to an empty string)
        message = kwargs.get("message", "")
        title = kwargs.get("title", message)  # If title is not provided, use message

        # Check if message is empty and log an error if so.
        if not message:
            self.log("Error: No message provided for media notification.")
            return

        self.notify_alexa_media(message, title)
        self.notify_alexa_monkey(message, title)
        self.notify_tts(message, title)

    def notify_tts(self, message, title=None):
        if len(self.__tts_devices) > 0:
            language = 'en-US'
            if self.__language == 'german':
                language = 'de-DE'
            for device in self.__tts_devices:
                self.log("Calling service tts/speak with device {} and message: {}".format(device, message))
                self.call_service(
                    "tts/speak",
                    entity_id="tts.piper",
                    cache=True,
                    media_player_entity_id=device,
                    message=message
                )

    def notify_alexa_media(self, message, title=None):
        if len(self.__alexa_media_devices) > 0:
            data = {"type":"announce","method":"all"}
            self.log("Calling service notify/alexa_media with message: {}".format(message))
            self.call_service(
                "notify/alexa_media", message=message, title=title, data=data, target=self.__alexa_media_devices)

    def notify_alexa_monkey(self, message, title=None):
        if len(self.__alexa_monkeys) > 0:
            for monkey in self.__alexa_monkeys:
                data = {"announcement":message,"monkey":monkey}
                self.log("Calling service rest_command/trigger_monkey with monkey {} and message: {}".format(monkey, message))
                self.call_service(
                    "rest_command/trigger_monkey", announcement=message, monkey=monkey)

    # def notify_mobile_app(self, message, title=None):

    def translate(self, message):
        return self.__translation[self.__language][message]

    def in_silent_mode(self):
        if self.__silent_control is None:
            return False
        if self.get_state(self.__silent_control) == 'on':
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

    def is_alarm_disarmed(self):
        return self.is_alarm_in_state('disarmed')

    def is_alarm_pending(self):
        return self.is_alarm_in_state('pending')

    def is_alarm_triggered(self):
        return self.is_alarm_in_state('triggered')

    def is_alarm_in_state(self, state):
        if self.__alarm_control_panel is None:
            return False
        if self.get_state(self.__alarm_control_panel) == state:
            return True
        else:
            return False

    def get_alarm_state(self):
        if self.__alarm_control_panel is None:
            return None
        return self.get_state(self.__alarm_control_panel)

    def is_time_in_arm_night_window(self):
        return self.now_is_between(self.__alarm_arm_night_after_time, self.__alarm_arm_night_before_time)

    def is_time_in_sleep_window(self):
        return self.now_is_between(self.__sleep_after_time, self.__sleep_before_time)

    def set_alarm_light_color(self, color_name="green", brightness_pct=100):
        for light in self.__alarm_lights:
            self.call_service(
                "light/turn_on", entity_id=light, color_name=color_name, brightness_pct=brightness_pct)

    def set_alarm_light_color_based_on_state(self):
        if self.is_alarm_disarmed():
            self.set_alarm_light_color("green", 15)
        elif self.is_alarm_armed_away():
            self.set_alarm_light_color("yellow", 25)
        elif self.is_alarm_armed_vacation():
            self.set_alarm_light_color("white", 25)
        elif self.is_alarm_armed_home():
            self.set_alarm_light_color("blue", 20)
        elif self.is_alarm_armed_night():
            self.set_alarm_light_color("blue", 10)
        elif self.is_alarm_triggered():
            self.set_alarm_light_color("red", 100)
        #elif self.is_alarm_pending():
        #

    def set_alarm_type(self, alarm_type):
        self.log("Setting alarm type to {}".format(alarm_type), level = "DEBUG")
        self.__alarm_type = alarm_type

    def get_alarm_type(self):
        return self.__alarm_type

    def add_alarm_message(self, message):
        self.log("Adding message {} to list of alarm messages".format(message), level = "DEBUG")
        if message not in self.__alarm_messages:
            self.__alarm_messages.append(message)

    def reset_alarm_messages(self):
        self.log("Resetting list of alarm messages", level = "DEBUG")
        self.__alarm_messages = []

    def get_alarm_messages(self):
        return self.__alarm_messages

    def flash_warning(self, kwargs):
        for light in self.__alarm_lights:
            self.toggle(light)
        self.__flash_count += 1
        self.log("Flash warning count {}".format(self.__flash_count))
        if self.__flash_count < 60:
            self.__flash_warning_handle = self.run_in(self.flash_warning, 1)

    def start_flash_warning(self, color_name="red", brightness_pct=100):
        self.stop_flash_warning()
        self.__flash_count = 0
        self.set_alarm_light_color(color_name, brightness_pct)
        self.log("Starting flash warning timer with color {} and brightnes {}".format(
            color_name, brightness_pct))
        self.__flash_warning_handle = self.run_in(self.flash_warning, 1)

    def stop_flash_warning(self):
        if self.__flash_warning_handle is not None:
            self.log("Stopping flash warning timer")
            self.cancel_timer(self.__flash_warning_handle)
            self.__flash_count = 60
            self.__flash_warning_handle = None

    def media_warning(self, kwargs):
        self.log("Alarm message count {}".format(len(self.get_alarm_messages())))
        self.media_warning_with_delay(self.get_alarm_messages())
        self.__media_count += 1
        self.log("Media warning count {}".format(self.__media_count))
        if self.__media_count < self.__media_warning_max_count:
            self.__media_warning_handle = self.run_in(self.media_warning, self.__media_warning_delay + len(self.get_alarm_messages() * 5))

    def media_warning_with_delay(self, messages, delay=5):
        """Send each message with a delay"""
        for i, message in enumerate(messages):
            self.run_in(self.notify_media, i * delay, message=message)

    def start_media_warning(self):
        self.stop_media_warning()
        self.__media_count = 0
        self.log("Starting media warning timer")
        self.__media_warning_handle = self.run_in(self.media_warning, self.__media_warning_inital_delay)

    def stop_media_warning(self):
        if self.__media_warning_handle is not None:
            self.log("Stopping media warning timer")
            self.cancel_timer(self.__media_warning_handle)
            self.__media_count = self.__media_warning_max_count
            self.__media_warning_handle = None

    def start_burglar_siren(self):
        if self.in_silent_mode():
            self.log("Suppressed siren because of silent mode")
            return

        for siren in self.__burglar_siren_switches:
            self.log("Turning on burglar siren {}".format(siren))
            self.turn_on(siren)

    def stop_burglar_siren(self):
        for siren in self.__burglar_siren_switches:
            self.log("Turning off burglar siren {}".format(siren))
            self.turn_off(siren)

    def start_fire_siren(self):
        for siren in self.__fire_siren_switches:
            self.log("Turning on fire siren {}".format(siren))
            self.turn_on(siren)

    def stop_fire_siren(self):
        for siren in self.__fire_siren_switches:
            self.log("Turning off fire siren {}".format(siren))
            self.turn_off(siren)

    def camera_snapshot(self, kwargs):
        if len(self.__cameras) == 0:
            return

        if self.__snap_count >= self.__snap_max_count:
            self.log("Camera snapshot max_count reached {}/{}".format(self.__snap_count, self.__snap_max_count))
            return

        for camera in self.__cameras:
            timestamp = str(datetime.datetime.now().strftime('%Y%m%d_%H%M%S%f'))
            filename = "{}/camera_snapshot_{}_{}.jpg".format(self.__camera_snapshot_path, camera, timestamp)
            self.call_service("camera/snapshot", entity_id=camera, filename=filename)

        self.__snap_count += 1
        self.log("Camera snapshot {} stored as {}".format(self.__snap_count, filename))
        if self.__snap_count < self.__snap_max_count:
            self.__camera_snapshot_handle = self.run_in(self.camera_snapshot, self.__snap_interval)

    def camera_snapshot_stored_callback(self, event_name, data, kwargs):
        self.log("Callback camera_snapshot_stored_callback from {}:{} {}".format(
            event_name, data['event_type'], data['path']))

        if (data['folder'] != self.__camera_snapshot_path):
            self.log("Ignoring file because its folder does not match the configured camera_snapshot_path")
            return

        matches = re.search(self.__camera_snapshot_regex, data['path'])

        if matches == None:
            self.log("Ignoring file because it does not match regex")
            return

        if(self.is_alarm_disarmed()):
            self.log("Ignoring file because alarm is disarmed")
            return
        if(self.is_alarm_armed_home()):
            self.log("Ignoring file because alarm is armed_home")
            return

        for user_id in self.__telegram_user_ids:
            self.log("Sending photo {} to user_id {}".format(data['path'], user_id))
            self.call_service('telegram_bot/send_photo',
                              title='*Alarm System*',
                              target=user_id,
                              file=data['path'],
                              disable_notification=True)


    def start_camera_snapshot(self, reason="default", max_count=3600, interval=1):
        if len(self.__cameras) == 0:
            return

        self.stop_camera_snapshot()
        self.__snap_count = 0
        self.__snap_max_count = max_count
        self.__snap_reason = reason
        self.__snap_start_timestamp = time.time()
        self.__snap_interval = interval
        self.log("Starting camera snapshot timer".format())
        self.__camera_snapshot_handle = self.run_in(self.camera_snapshot, 1)

    def stop_camera_snapshot(self):
        if len(self.__cameras) == 0:
            return

        if self.__camera_snapshot_handle is not None:
            self.log("Stopping camera snapshot timer")
            self.cancel_timer(self.__camera_snapshot_handle)
            self.__snap_count = self.__snap_max_count
            self.__camera_snapshot_handle = None

    def alarm_state_triggered_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_state_triggered from {}:{} {}->{}".format(entity, attribute, old, new))

        self.stop_flash_warning()
        self.set_alarm_light_color_based_on_state()
        self.start_camera_snapshot("alarm_state_triggered")

        self.log("Alarm reason is {}".format(self.get_alarm_type()))

        if self.get_alarm_type() == 'burglar':
            self.start_burglar_siren()
        if self.get_alarm_type() == 'fire':
            self.start_fire_siren()

        message = self.translate("alarm_system_triggered")
        self.notify(message)

        self.start_media_warning()

        if self.__notify_service is not None:
            self.call_service(self.__notify_service, title=self.__notify_title.format(self.get_alarm_type()))

    def alarm_state_from_armed_home_to_pending_callback(self, entity, attribute, old, new, kwargs):
        self.log("Callback alarm_state_from_armed_home_to_pending from {}:{} {}->{}".format(
            entity, attribute, old, new))

        self.start_flash_warning("red")
        self.start_camera_snapshot("alarm_state_from_armed_home_to_pending")

    def alarm_state_from_armed_away_to_pending_callback(self, entity, attribute, old, new, kwargs):
        self.log("Callback alarm_state_from_armed_away_to_pending from {}:{} {}->{}".format(
            entity, attribute, old, new))

        self.start_flash_warning("red")
        self.start_camera_snapshot("alarm_state_from_armed_away_to_pending")

    def alarm_state_from_disarmed_to_pending_callback(self, entity, attribute, old, new, kwargs):
        self.log("Callback alarm_state_from_disarmed_to_pending from {}:{} {}->{}".format(
            entity, attribute, old, new))

        self.start_flash_warning("yellow", 50)
        self.start_camera_snapshot("alarm_state_from_disarmed_to_pending")

    def alarm_state_disarmed_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_state_disarmed from {}:{} {}->{}".format(entity, attribute, old, new))

        self.stop_flash_warning()
        self.start_camera_snapshot("alarm_state_disarmed", 10, 60)
        self.stop_sensor_listeners()
        self.set_alarm_light_color_based_on_state()
        self.stop_fire_siren()
        self.stop_burglar_siren()
        self.stop_media_warning()
        self.reset_alarm_messages()

        message = self.translate("alarm_system_disarmed")
        self.notify(message, prio=1)

    def alarm_state_armed_away_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_state_armed_away from {}:{} {}->{}".format(entity, attribute, old, new))

        self.stop_flash_warning()
        self.start_camera_snapshot("alarm_state_armed_away", 99999, 300)
        self.stop_sensor_listeners()
        self.start_armed_away_binary_sensor_listeners()
        self.set_alarm_light_color_based_on_state()
        self.stop_fire_siren()
        self.stop_burglar_siren()
        self.stop_media_warning()
        self.reset_alarm_messages()

        message = self.translate("alarm_system_armed_away")
        self.notify(message, prio=1)

    def alarm_state_armed_home_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_state_armed_home from {}:{} {}->{}".format(entity, attribute, old, new))

        self.stop_flash_warning()
        self.start_camera_snapshot("alarm_state_armed_home", 10, 60)
        self.stop_sensor_listeners()
        self.start_armed_home_binary_sensor_listeners()
        self.set_alarm_light_color_based_on_state()
        self.stop_fire_siren()
        self.stop_burglar_siren()
        self.stop_media_warning()
        self.reset_alarm_messages()

        message = self.translate("alarm_system_armed_home")
        self.notify(message, prio=1)

    def alarm_state_armed_night_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_state_armed_home from {}:{} {}->{}".format(entity, attribute, old, new))

        self.stop_flash_warning()
        self.start_camera_snapshot("alarm_state_armed_night", 10, 60)
        self.stop_sensor_listeners()
        self.start_armed_home_binary_sensor_listeners()
        self.set_alarm_light_color_based_on_state()
        self.stop_fire_siren()
        self.stop_burglar_siren()
        self.stop_media_warning()
        self.reset_alarm_messages()

        message = self.translate("alarm_system_armed_night")
        self.notify(message, prio=1)

    def trigger_alarm_while_armed_away_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback trigger_alarm_while_armed_away from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.is_alarm_armed_away() == False and self.is_alarm_armed_vacation() == False and self.is_alarm_triggered() == False and self.is_alarm_pending == False):
            self.log("Ignoring state {} of {} because alarm system is in state {}".format(
                new, entity, self.get_alarm_state()))
            return

        if(self.count_home_device_trackers() > 0):
            self.log("Ignoring state {} of {} because {} device_trackers are still at home".format(
                new, entity, self.count_home_device_trackers()))
            return

        self.set_alarm_type('burglar')

        message = self.translate("burglar_alert").format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)

        self.add_alarm_message(message)

        self.log("Calling service alarm_control_panel/alarm_trigger")

        self.call_service("alarm_control_panel/alarm_trigger",
                          entity_id=self.__alarm_control_panel)

    def trigger_alarm_while_armed_home_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback trigger_alarm_while_armed_home from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.is_alarm_armed_home() == False and self.is_alarm_armed_night() == False and self.is_alarm_triggered() == False and self.is_alarm_pending == False):
            self.log("Ignoring state {} of {} because alarm system is in state {}".format(
                new, entity, self.get_alarm_state()))
            return

        self.set_alarm_type('burglar')

        message = self.translate("burglar_alert").format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)

        self.add_alarm_message(message)

        self.log("Calling service alarm_control_panel/alarm_trigger")

        self.call_service("alarm_control_panel/alarm_trigger",
                          entity_id=self.__alarm_control_panel)

    def trigger_alarm_fire_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback trigger_alarm_fire from {}:{} {}->{}".format(entity, attribute, old, new))

        self.set_alarm_type('fire')

        message = self.translate("fire_alert").format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)

        self.add_alarm_message(message)

        self.log("Calling service alarm_control_panel/alarm_trigger")

        self.call_service("alarm_control_panel/alarm_trigger",
                          entity_id=self.__alarm_control_panel)

    def trigger_alarm_fire_temperature_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback trigger_alarm_fire_temperature from {}:{} {}->{}".format(entity, attribute, old, new))

        if(new == 'unknown' or new == 'unavailable'):
            self.log("Ignoring state {} of {}".format(
                new, entity))
            return

        if(float(new) < self.__fire_temperature_threshold):
            self.log("Ignoring state {} of {} because value is below treshhold {}".format(
                new, entity, self.__fire_temperature_threshold))
            return

        self.set_alarm_type('fire')

        message = self.translate("fire_temperature_alert").format(self.get_state(entity, attribute = "friendly_name"), new)
        self.notify(message)

        self.add_alarm_message(message)

        self.log("Calling service alarm_control_panel/alarm_trigger")

        self.call_service("alarm_control_panel/alarm_trigger",
                          entity_id=self.__alarm_control_panel)

    def trigger_alarm_water_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback trigger_alarm_fire from {}:{} {}->{}".format(entity, attribute, old, new))

        self.set_alarm_type('water')

        message = self.translate("water_leak_alert").format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)

        self.add_alarm_message(message)

        self.log("Calling service alarm_control_panel/alarm_trigger")

        self.call_service("alarm_control_panel/alarm_trigger",
                          entity_id=self.__alarm_control_panel)

    def debug_event(self, event_name, data, kwargs):
        self.log(
            "Debug event {}:{} {}".format(event_name, data, kwargs))

    def alarm_button_callback(self, event_name, data, kwargs):
        #self.debug(
        #    "Callback alarm_button_callback from event {}:{} {}".format(event_name, data, kwargs))

        # entity_id
        #self.log(data['new_state']['attributes']['event_type'])

        event_type = data['new_state']['attributes']['event_type']
        entity_id = data['entity_id']

        self.log("Callback alarm_button_callback from event {}:{}".format(entity_id, event_type))

        if event_type == "single":
            self.button_arm_home(entity_id)
        elif event_type == "double":
            self.button_arm_away(entity_id)
        elif event_type == "triple":
            self.button_disarm(entity_id)
        elif event_type == "quadruple":
            self.button_disarm(entity_id)
        elif event_type == "hold":
            self.button_trigger_alarm(entity_id)
        else:
            self.log("Ignoring event")

    def button_arm_away(self, entity):

        if(self.is_alarm_disarmed() == False):
            self.log("Ignoring call because alarm system is in state {}".format(
                self.get_alarm_state()))
            return

        mode = "arm_away"
        if(self.in_vacation_mode()):
            mode = "arm_vacation"

        message = self.translate("button_{}".format(mode)).format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)

        self.log("Calling service alarm_control_panel/alarm_{}".format(mode))

        self.call_service("alarm_control_panel/alarm_{}".format(mode),
                          entity_id=self.__alarm_control_panel, code=self.__alarm_pin)

    def button_arm_home(self, entity):

        if(self.is_alarm_disarmed() == False):
            self.log("Ignoring call because alarm system is in state {}".format(
                self.get_alarm_state()))
            return

        message = self.translate("button_arm_home").format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)

        self.log("Calling service alarm_control_panel/alarm_arm_home")

        self.call_service("alarm_control_panel/alarm_arm_home",
                          entity_id=self.__alarm_control_panel, code=self.__alarm_pin)

    def button_disarm(self, entity):

        if(self.is_alarm_disarmed()):
            self.log("Ignoring call because alarm system is in state {}".format(
                self.get_alarm_state()))
            return

        self.set_alarm_type(None)

        message = self.translate("button_disarm").format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)

        self.log("Calling service alarm_control_panel/alarm_disarm")

        self.call_service("alarm_control_panel/alarm_disarm",
                          entity_id=self.__alarm_control_panel, code=self.__alarm_pin)

    def button_trigger_alarm(self, entity):
        self.log("Trigger alarm using button")

        self.set_alarm_type('burglar')

        message = self.translate("burglar_alert").format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)
        self.add_alarm_message(message)

        self.log("Calling service alarm_control_panel/alarm_trigger")

        self.call_service("alarm_control_panel/alarm_trigger",
                          entity_id=self.__alarm_control_panel)

    def alarm_arm_away_auto_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_arm_away_auto from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.is_alarm_disarmed() == False):
            self.log("Ignoring state {} of {} because alarm system is in state {}".format(
                new, entity, self.get_alarm_state()))
            return

        if(self.count_home_device_trackers() > 0):
            self.log("Ignoring state {} of {} because {} device_trackers are still at home".format(
                new, entity, self.count_home_device_trackers()))
            return

        if(self.in_guest_mode()):
            self.log("Ignoring state {} of {} because home is in guest mode".format(
                new, entity))
            return

        mode = "arm_away"
        if(self.in_vacation_mode()):
            mode = "arm_vacation"

        message = self.translate("auto_{}_person".format(mode)).format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)

        self.log("Calling service alarm_control_panel/alarm_{}".format(mode))

        self.call_service("alarm_control_panel/alarm_{}".format(mode),
                          entity_id=self.__alarm_control_panel, code=self.__alarm_pin)

    def alarm_disarm_auto_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_disarm_auto from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.is_alarm_disarmed()):
            self.log("Ignoring state {} of {} because alarm system is in state {}".format(
                new, entity, self.get_alarm_state()))
            return

        message = self.translate("auto_disarm_person").format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message)

        self.log("Calling service alarm_control_panel/alarm_disarm")

        self.call_service("alarm_control_panel/alarm_disarm",
                          entity_id=self.__alarm_control_panel, code=self.__alarm_pin)

    def alarm_arm_night_auto_state_change_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_arm_night_auto_state_change from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.is_alarm_disarmed() == False):
            self.log("Ignoring state {} of {} because alarm system is in state {}".format(
                new, entity, self.get_alarm_state()))
            return

        if(self.count_home_device_trackers() == 0):
            self.log("Ignoring state {} of {} because all {} device_trackers are still away".format(
                new, entity, self.count_not_home_device_trackers()))
            return

        if(self.in_guest_mode()):
            self.log("Ignoring state {} of {} because home is in guest mode".format(
                new, entity))
            return

        if(self.in_vacation_mode()):
            self.log("Ignoring state {} of {} because home is in vacation mode".format(
                new, entity))
            return

        if(self.is_time_in_arm_night_window() == False):
            self.log("Ignoring state {} of {} because we are not within arm night time window".format(
                new, entity))
            return

        message = self.translate("auto_arm_night_person").format(self.get_state(entity, attribute = "friendly_name"))
        self.notify(message, prio=1)

        self.log("Calling service alarm_control_panel/alarm_arm_night")

        self.call_service("alarm_control_panel/alarm_arm_night",
                          entity_id=self.__alarm_control_panel, code=self.__alarm_pin)

    def alarm_arm_night_auto_timer_callback(self, kwargs):
        self.log(
            "Callback alarm_arm_night_auto_timer".format())

        if(self.is_alarm_disarmed() == False):
            self.log("Ignoring arm night timer because alarm system is in state {}".format(
                self.get_alarm_state()))
            return

        if(self.count_home_device_trackers() == 0):
            self.log("Ignoring arm night timer because all {} device_trackers are still away".format(
                self.count_not_home_device_trackers()))
            return

        if(self.in_guest_mode()):
            self.log("Ignoring arm night timer because home is in guest mode")
            return

        if(self.in_vacation_mode()):
            self.log("Ignoring arm night timer because home is in vacation mode")
            return

        if(self.is_time_in_arm_night_window() == False):
            self.log("Ignoring arm night timer because we are not within arm home time window".format())
            return

        message = self.translate("auto_arm_night_schedule")
        self.notify(message, prio=1)

        self.log("Calling service alarm_control_panel/alarm_arm_night")

        self.call_service("alarm_control_panel/alarm_arm_night",
                          entity_id=self.__alarm_control_panel, code=self.__alarm_pin)

    def alarm_disarm_night_auto_timer_callback(self, kwargs):
        self.log(
            "Callback alarm_disarm_night_auto_timer".format())

        if(self.is_alarm_armed_night() == False):
            self.log("Ignoring disarm night timer because alarm system is in state {}".format(
                self.get_alarm_state()))
            return

        message = self.translate("auto_disarm_schedule")
        self.notify(message, prio=1)

        self.log("Calling service alarm_control_panel/alarm_disarm")

        self.call_service("alarm_control_panel/alarm_disarm",
                          entity_id=self.__alarm_control_panel, code=self.__alarm_pin)
