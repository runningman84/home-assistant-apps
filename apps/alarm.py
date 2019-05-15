import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime
import time
import os

#
# AlarmSystem App
#
# Args:
#


class AlarmSystem(hass.Hass):

    def initialize(self):
        self.log("Hello from AlarmSystem")

        # setup sane defaults
        self._armed_home_sensors = self.args.get("armed_home_sensors", [])
        self._armed_away_sensors = self.args.get("armed_away_sensors", [])
        self._device_trackers = self.args.get("device_trackers", [])
        self._vacation_control = self.args.get("vacation_control", None)
        self._guest_control = self.args.get("guest_control", None)
        self._alarm_control_panel = self.args.get(
            "alarm_control_panel", "alarm_control_panel.ha_alarm")
        self._alarm_control_buttons = self.args.get(
            "alarm_control_buttons", [])
        self._alarm_lights = self.args.get("alarm_lights", [])
        self._alarm_pin = self.args.get("alarm_pin", None)
        self._alarm_volume_control = self.args.get(
            "alarm_volume_control", None)
        self._info_volume_control = self.args.get("info_volume_control", None)
        self._silent_control = self.args.get("silent_control", None)
        self._notify_service = self.args.get("notify_service", None)
        self._notify_title = self.args.get(
            "notify_title", "AlarmSystem triggered, possible intruder")
        self._cameras = self.args.get("cameras", [])
        self._camera_snapshot_path = self.args.get("camera_snapshot_path", '/camera')
        self._telegram_user_ids = self.args.get("telegram_user_ids",[])

        # xiaomi specific
        self._xiaomi_aqara_gw_mac = self.args.get("xiaomi_aqara_gw_mac", None)
        self._xiaomi_aqara_trggered_ringtone_id = self.args.get(
            "xiaomi_aqara_trggered_ringtone_id", 2)
        self._xiaomi_aqara_pending_ringtone_id = self.args.get(
            "xiaomi_aqara_pending_ringtone_id", 10)
        self._xiaomi_aqara_disarmed_ringtone_id = self.args.get(
            "xiaomi_aqara_disarmed_ringtone_id", 11)

        # log current config
        self.log("Got armed_home sensors {}".format(
            self._armed_home_sensors))
        self.log("Got armed_away sensors {}".format(
            self._armed_away_sensors))
        self.log("Got device trackers {}".format(self._device_trackers))
        self.log("Got {} device_trackers home and {} device_trackers not home".format(
            self.count_home_device_trackers(), self.count_not_home_device_trackers()))
        self.log("Got guest_mode {}".format(self.in_guest_mode()))
        self.log("Got vacation_mode {}".format(self.in_vacation_mode()))
        self.log("Got silent mode {}".format(self.in_silent_mode()))
        self.log("Got info volume {}".format(self.get_info_volume()))
        self.log("Got alarm volume {}".format(self.get_alarm_volume()))
        self.log("Got notify service {}".format(self._notify_service))
        self.log("Got alarm state {}".format(self.get_alarm_state()))

        self.listen_state(self.alarm_state_triggered_callback,
                          self._alarm_control_panel, new="triggered")
        self.listen_state(self.alarm_state_from_armed_home_to_pending_callback,
                          self._alarm_control_panel, old="armed_home", new="pending")
        self.listen_state(self.alarm_state_from_armed_away_to_pending_callback,
                          self._alarm_control_panel, old="armed_away", new="pending")
        self.listen_state(self.alarm_state_from_disarmed_to_pending_callback,
                          self._alarm_control_panel, old="disarmed", new="pending")
        self.listen_state(self.alarm_state_disarmed_callback,
                          self._alarm_control_panel, new="disarmed")
        self.listen_state(self.alarm_state_armed_away_callback,
                          self._alarm_control_panel, new="armed_away")
        self.listen_state(self.alarm_state_armed_home_callback,
                          self._alarm_control_panel, new="armed_home")

        for button in self._alarm_control_buttons:
            self.listen_event(self.alarm_arm_home_button_callback,
                              'click', entity_id=button, click_type="single")
            self.listen_event(self.alarm_disarm_button_callback,
                              'click', entity_id=button, click_type="double")
            self.listen_event(self.alarm_arm_away_button_callback,
                              'click', entity_id=button, click_type="long_click_press")

        # auto arm and disarm
        i = 0
        for sensor in self._device_trackers:
            self.listen_state(self.alarm_arm_away_auto_callback, sensor,
                              new="not_home", duration=15 * 60 + i)
            self.listen_state(self.alarm_disarm_auto_callback,
                              sensor, new="home", duration=i)
            i += 1

        self._flash_warning_handle = None
        self._camera_snapshot_handle = None
        self._flash_count = 0
        self._snap_count = 0
        self._sensor_handles = {}
        self.set_alarm_light_color_based_on_state()

        # FIXME
        #runtime = datetime.time(0, 0, 0)
        #self.run_hourly(self.set_alarm_light_color_based_on_state, runtime)

    def start_armed_home_sensors_listener(self):
        for sensor in self._armed_home_sensors:
            self._sensor_handles[sensor] = self.listen_state(
                self.trigger_alarm_while_armed_home_callback, sensor, new="on", old="off")

    def start_armed_away_sensors_listener(self):
        for sensor in self._armed_away_sensors:
            self._sensor_handles[sensor] = self.listen_state(
                self.trigger_alarm_while_armed_away_callback, sensor, new="on", old="off")

    def stop_sensors_listener(self):
        for handle in self._sensor_handles:
            if self._sensor_handles[handle] is not None:
                self.cancel_listen_state(self._sensor_handles[handle])
                self._sensor_handles[handle] = None

    def count_doors_and_windows(self, state):
        count = 0
        for sensor in self._door_window_sensors:
            if self.get_state(sensor) == state:
                count = count + 1
        return count

    def count_open_doors_and_windows(self):
        return self.count_doors_and_windows("on")

    def count_closed_doors_and_windows(self):
        return self.count_doors_and_windows("off")

    def count_device_trackers(self, state):
        count = 0
        for sensor in self._device_trackers:
            if self.get_state(sensor) == state:
                count = count + 1
        return count

    def count_home_device_trackers(self):
        return self.count_device_trackers("home")

    def count_not_home_device_trackers(self):
        return self.count_device_trackers("not_home")

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

    def get_alarm_volume(self):
        if self._alarm_volume_control is None:
            return 99
        return int(float(self.get_state(self._alarm_volume_control)))

    def get_info_volume(self):
        if self._info_volume_control is None:
            return 10
        return int(float(self.get_state(self._info_volume_control)))

    def get_xiaomi_aqara_gw_mac(self):
        return self._xiaomi_aqara_gw_mac

    def get_xiaomi_aqara_trggered_ringtone_id(self):
        return self._xiaomi_aqara_trggered_ringtone_id

    def get_xiaomi_aqara_pending_ringtone_id(self):
        return self._xiaomi_aqara_pending_ringtone_id

    def get_xiaomi_aqara_disarmed_ringtone_id(self):
        return self._xiaomi_aqara_disarmed_ringtone_id

    def in_silent_mode(self):
        if self._silent_control is None:
            return False
        if self.get_state(self._silent_control) == 'on':
            return True
        else:
            return False

    def is_alarm_armed_away(self):
        return self.is_alarm_in_state('armed_away')

    def is_alarm_armed_home(self):
        return self.is_alarm_in_state('armed_home')

    def is_alarm_disarmed(self):
        return self.is_alarm_in_state('disarmed')

    def is_alarm_pending(self):
        return self.is_alarm_in_state('pending')

    def is_alarm_triggered(self):
        return self.is_alarm_in_state('triggered')

    def is_alarm_in_state(self, state):
        if self._alarm_control_panel is None:
            return False
        if self.get_state(self._alarm_control_panel) == state:
            return True
        else:
            return False

    def get_alarm_state(self):
        if self._alarm_control_panel is None:
            return None
        return self.get_state(self._alarm_control_panel)

    def set_alarm_light_color(self, color_name="green", brightness_pct=100):
        for light in self._alarm_lights:
            self.call_service(
                "light/turn_on", entity_id=light, color_name=color_name, brightness_pct=brightness_pct)

    def set_alarm_light_color_based_on_state(self):
        if self.is_alarm_disarmed():
            self.set_alarm_light_color("green", 15)
        elif self.is_alarm_armed_away():
            self.set_alarm_light_color("yellow", 25)
        elif self.is_alarm_armed_home():
            self.set_alarm_light_color("blue", 20)
        elif self.is_alarm_triggered():
            self.set_alarm_light_color("red", 100)
        #elif self.is_alarm_pending():
        #

    def flash_warning(self, kwargs):
        for light in self._alarm_lights:
            self.toggle(light)
        self._flash_count += 1
        self.log("Flash warning count {}".format(self._flash_count))
        if self._flash_count < 60:
            self._flash_warning_handle = self.run_in(self.flash_warning, 1)

    def start_flash_warning(self, color_name="red", brightness_pct=100):
        self.stop_flash_warning()
        self._flash_count = 0
        self.set_alarm_light_color(color_name, brightness_pct)
        self.log("Starting flash warning timer with color {} and brightnes {}".format(
            color_name, brightness_pct))
        self._flash_warning_handle = self.run_in(self.flash_warning, 1)

    def stop_flash_warning(self):
        if self._flash_warning_handle is not None:
            self.log("Stopping flash warning timer")
            self.cancel_timer(self._flash_warning_handle)
            self._flash_count = 60
            self._flash_warning_handle = None

    def camera_snapshot(self, kwargs):
        if len(self._cameras) == 0:
            return

        if self._snap_count >= self._snap_max_count:
            self.log("Camera snapshot max_count reached {}/{}".format(self._snap_count, self._snap_max_count))
            return

        for camera in self._cameras:
            timestamp = str(time.time())
            filename = self._camera_snapshot_path + "/" + self._snap_storage_prefix + "/" + camera + "_" + timestamp + ".jpg"
            linkid = self._snap_count % 20
            lnksrc = self._snap_storage_prefix + "/" + camera + "_" + timestamp + ".jpg"
            linkdst = self._camera_snapshot_path + "/" + camera + "_latest_" + str(linkid) + ".jpg"
            self.call_service("camera/snapshot",
                              entity_id=camera, filename=filename)
            #os.symlink(filename, linkname)
            os.system('ln -sf "' + lnksrc + '" "' + linkdst + '"')

            if self._snap_count < 3:
                self.handle = self.run_in(self.send_camera_snapshot, 3, filename = filename)

        self._snap_count += 1
        self.log("Camera snapshot {} stored as {}".format(self._snap_count, filename))
        if self._snap_count < self._snap_max_count:
            self._camera_snapshot_handle = self.run_in(self.camera_snapshot, self._snap_interval)

    def send_camera_snapshot(self, kwargs):
        if len(self._cameras) == 0:
            return

        for user_id in self._telegram_user_ids:
            self.log("Sending photo {} to user_id {}".format(kwargs['filename'], user_id))
            self.call_service('telegram_bot/send_photo',
                              title='*Alarm System*',
                              target=user_id,
                              file=kwargs['filename'],
                              caption='Webcam picture',
                              disable_notification=True)

        #self.handle = self.run_in(self.run_in_c, title = "run_in5")

    def start_camera_snapshot(self, reason="default", max_count=3600, interval=1):
        if len(self._cameras) == 0:
            return

        self.stop_camera_snapshot()
        self._snap_count = 0
        self._snap_max_count = max_count
        self._snap_reason = reason
        self._snap_start_timestamp = time.time()
        self._snap_interval = interval
        self._snap_storage_prefix = self._snap_reason + "/" + str(self._snap_start_timestamp)
        os.system('mkdir -p "' + self._camera_snapshot_path + "/" + self._snap_storage_prefix + '"')
        self.log("Starting camera snapshot timer".format())
        self._camera_snapshot_handle = self.run_in(self.camera_snapshot, 1)

    def stop_camera_snapshot(self):
        if len(self._cameras) == 0:
            return

        if self._camera_snapshot_handle is not None:
            self.log("Stopping camera snapshot timer")
            self.cancel_timer(self._camera_snapshot_handle)
            self._snap_count = self._snap_max_count
            self._camera_snapshot_handle = None

    def alarm_state_triggered_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_state_triggered from {}:{} {}->{}".format(entity, attribute, old, new))

        if self.get_xiaomi_aqara_gw_mac() is not None and self.in_silent_mode() == False:
            self.call_service("xiaomi_aqara/play_ringtone",
                              ringtone_id=self.get_xiaomi_aqara_trggered_ringtone_id(), ringtone_vol=self.get_alarm_volume(), gw_mac=self.get_xiaomi_aqara_gw_mac())

        self.stop_flash_warning()
        self.set_alarm_light_color_based_on_state()
        self.start_camera_snapshot("alarm_state_triggered")

        if self._notify_service is not None:
            self.call_service(self._notify_service, title=self._notify_title)

    def alarm_state_from_armed_home_to_pending_callback(self, entity, attribute, old, new, kwargs):
        self.log("Callback alarm_state_from_armed_home_to_pending from {}:{} {}->{}".format(
            entity, attribute, old, new))

        if self.get_xiaomi_aqara_gw_mac() is not None and self.in_silent_mode() == False:
            self.call_service("xiaomi_aqara/play_ringtone",
                              ringtone_id=self.get_xiaomi_aqara_pending_ringtone_id(), ringtone_vol=self.get_info_volume(), gw_mac=self.get_xiaomi_aqara_gw_mac())

        self.start_flash_warning("red")
        self.start_camera_snapshot("alarm_state_from_armed_home_to_pending")

    def alarm_state_from_armed_away_to_pending_callback(self, entity, attribute, old, new, kwargs):
        self.log("Callback alarm_state_from_armed_away_to_pending from {}:{} {}->{}".format(
            entity, attribute, old, new))

        if self.get_xiaomi_aqara_gw_mac() is not None and self.in_silent_mode() == False:
            self.call_service("xiaomi_aqara/play_ringtone",
                              ringtone_id=self.get_xiaomi_aqara_pending_ringtone_id(), ringtone_vol=self.get_info_volume(), gw_mac=self.get_xiaomi_aqara_gw_mac())

        self.start_flash_warning("red")
        self.start_camera_snapshot("alarm_state_from_armed_away_to_pending")

    def alarm_state_from_disarmed_to_pending_callback(self, entity, attribute, old, new, kwargs):
        self.log("Callback alarm_state_from_disarmed_to_pending from {}:{} {}->{}".format(
            entity, attribute, old, new))

        if self.get_xiaomi_aqara_gw_mac() is not None and self.in_silent_mode() == False:
            self.call_service("xiaomi_aqara/play_ringtone",
                              ringtone_id=self.get_xiaomi_aqara_pending_ringtone_id(), ringtone_vol=self.get_info_volume(), gw_mac=self.get_xiaomi_aqara_gw_mac())

        self.start_flash_warning("yellow", 50)
        self.start_camera_snapshot("alarm_state_from_disarmed_to_pending")

    def alarm_state_disarmed_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_state_disarmed from {}:{} {}->{}".format(entity, attribute, old, new))

        if self.get_xiaomi_aqara_gw_mac() is not None and self.in_silent_mode() == False:
            self.call_service("xiaomi_aqara/stop_ringtone",
                              gw_mac=self.get_xiaomi_aqara_gw_mac())

            self.call_service("xiaomi_aqara/play_ringtone",
                              ringtone_id=self.get_xiaomi_aqara_disarmed_ringtone_id(), ringtone_vol=self.get_info_volume(), gw_mac=self.get_xiaomi_aqara_gw_mac())

        self.stop_flash_warning()
        self.start_camera_snapshot("alarm_state_disarmed", 10, 60)
        self.stop_sensors_listener()
        self.set_alarm_light_color_based_on_state()

    def alarm_state_armed_away_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_state_armed_away from {}:{} {}->{}".format(entity, attribute, old, new))

        if self.get_xiaomi_aqara_gw_mac() is not None and self.in_silent_mode() == False:
            self.call_service("xiaomi_aqara/stop_ringtone",
                              gw_mac=self.get_xiaomi_aqara_gw_mac())

        self.stop_flash_warning()
        self.start_camera_snapshot("alarm_state_armed_away", 99999, 300)
        self.stop_sensors_listener()
        self.start_armed_away_sensors_listener()
        self.set_alarm_light_color_based_on_state()


    def alarm_state_armed_home_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_state_armed_home from {}:{} {}->{}".format(entity, attribute, old, new))

        if self.get_xiaomi_aqara_gw_mac() is not None and self.in_silent_mode() == False:
            self.call_service("xiaomi_aqara/stop_ringtone",
                              gw_mac=self.get_xiaomi_aqara_gw_mac())

        self.stop_flash_warning()
        self.start_camera_snapshot("alarm_state_armed_home", 10, 60)
        self.stop_sensors_listener()
        self.start_armed_home_sensors_listener()
        self.set_alarm_light_color_based_on_state()

    def trigger_alarm_while_armed_away_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback trigger_alarm_while_armed_away from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.is_alarm_armed_away() == False):
            self.log("Ignoring status {} of {} because alarm system is in state {}".format(
                new, entity, self.get_alarm_state()))
            return

        if(self.count_home_device_trackers() > 0):
            self.log("Ignoring status {} of {} because {} device_trackers are still at home".format(
                new, entity, self.count_home_device_trackers()))
            return

        for user_id in self._telegram_user_ids:
            msg = "{} state changed from {} to {}".format(self.get_state(entity, attribute = "friendly_name"), old, new)
            self.log("Sending message {} to user_id {}".format(msg, user_id))
            self.call_service('telegram_bot/send_message',
                              title='*Alarm System*',
                              target=user_id,
                              message=msg,
                              disable_notification=True)

        self.call_service("alarm_control_panel/alarm_trigger",
                          entity_id=self._alarm_control_panel)

    def trigger_alarm_while_armed_home_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback trigger_alarm_while_armed_home from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.is_alarm_armed_home() == False):
            self.log("Ignoring status {} of {} because alarm system is in state {}".format(
                new, entity, self.get_alarm_state()))
            return

        for user_id in self._telegram_user_ids:
            msg = "{} state changed from {} to {}".format(self.get_state(entity, attribute = "friendly_name"), old, new)
            self.log("Sending message {} to user_id {}".format(msg, user_id))
            self.call_service('telegram_bot/send_message',
                              title='*Alarm System*',
                              target=user_id,
                              message=msg,
                              disable_notification=True)

        self.call_service("alarm_control_panel/alarm_trigger",
                          entity_id=self._alarm_control_panel)

    def alarm_arm_away_button_callback(self, event_name, data, kwargs):
        self.log("Callback alarm_arm_away_button_callback from {}:{} {}".format(
            event_name, data['entity_id'], data['click_type']))

        if(self.is_alarm_disarmed() == False):
            self.log("Ignoring event {} of {} because alarm system is in state {}".format(
                event_name, data['entity_id'], self.get_alarm_state()))
            return

        self.call_service("alarm_control_panel/alarm_arm_away",
                          entity_id=self._alarm_control_panel, code=self._alarm_pin)

    def alarm_disarm_button_callback(self, event_name, data, kwargs):
        self.log("Callback alarm_disarm_button_callback from {}:{} {}".format(
            event_name, data['entity_id'], data['click_type']))

        if(self.is_alarm_disarmed()):
            self.log("Ignoring event {} of {} because alarm system is in state {}".format(
                event_name, data['entity_id'], self.get_alarm_state()))
            return

        self.call_service("alarm_control_panel/alarm_disarm",
                          entity_id=self._alarm_control_panel, code=self._alarm_pin)

    def alarm_arm_home_button_callback(self, event_name, data, kwargs):
        self.log("Callback alarm_arm_home_button from {}:{} {}".format(
            event_name, data['entity_id'], data['click_type']))

        if(self.is_alarm_disarmed() == False):
            self.log("Ignoring event {} of {} because alarm system is in state {}".format(
                event_name, data['entity_id'], self.get_alarm_state()))
            return

        self.call_service("alarm_control_panel/alarm_arm_home",
                          entity_id=self._alarm_control_panel, code=self._alarm_pin)

    def alarm_arm_away_auto_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_arm_away_auto from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.is_alarm_disarmed() == False):
            self.log("Ignoring status {} of {} because alarm system is in state {}".format(
                new, entity, self.get_alarm_state()))
            return

        if(self.count_home_device_trackers() > 0):
            self.log("Ignoring status {} of {} because {} device_trackers are still at home".format(
                new, entity, self.count_home_device_trackers()))
            return

        if(self.in_guest_mode()):
            self.log("Ignoring status {} of {} because {} we have guests".format(
                new, entity, self.count_home_device_trackers()))
            return

        self.call_service("alarm_control_panel/alarm_arm_away",
                          entity_id=self._alarm_control_panel, code=self._alarm_pin)

    def alarm_disarm_auto_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_disarm_auto from {}:{} {}->{}".format(entity, attribute, old, new))

        if(self.is_alarm_armed_away() == False):
            self.log("Ignoring status {} of {} because alarm system is in state {}".format(
                new, entity, self.get_alarm_state()))
            return

        self.call_service("alarm_control_panel/alarm_disarm",
                          entity_id=self._alarm_control_panel, code=self._alarm_pin)
