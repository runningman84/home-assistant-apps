# home-assistant-apps
home assistant apps based on appdaemon

AlarmSystem
============

This system work with any light system (should support color) and with any sensors who report on/off values. I have tested it with xiaomi hub, sensors, buttons.

Key | Description | Default
------------ | ------------- | -------------
device_trackers | list of tracked devices (for auto arming / disarming) | []
armed_home_sensors | list of sensors to monitor (like doors, motion, sensors) in case you are home | []
armed_away_sensors | list of sensors to monitor (like doors, motion, sensors) in case you are away | []
alarm_control_buttons | list of buttons to control (single click arm_away, double click disarm, long pres arm_home) | []
alarm_lights | list of lights to flash (red color for triggered alarm) | []
vacation_control | not used (tbd)
guest_control | input boolean to configure a babysitter mode which does not auto arm | None
silent_control | input boolean to mute the alarm sound | None
alarm_volume_control | input_number for alarm volume | None
info_volume_control | input_number for input volume | None
xiaomi_aqara_gw_mac | xiaomi_aqara_gw_mac to play ringtones | None
notify_service | script to call for notification | None
notify_title | title parameter for script | AlarmSystem triggered, possible intruder
