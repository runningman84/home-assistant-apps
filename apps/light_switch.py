import appdaemon.plugins.hass.hassapi as hass
import datetime
import time
import re
import inspect

#
# LightSwitch App
#
# Args:
#


class LightSwitch(hass.Hass):

    def initialize(self):
        self.log("Hello from LightSwitch")

        self.__remotes = self.args.get("remotes", [])
        self.__lights = self.args.get("lights", [])
        self.__lights_left = self.args.get("lights_left", [])
        self.__lights_right = self.args.get("lights_right", [])

        for remote in self.__remotes:
            self.listen_event(self.remote_callback, entity_id=remote, event_type="state_changed", event="state_changed")

    def debug_event(self, event_name, data, kwargs):
        self.log(f"Debug event {event_name}:{data} {kwargs}")

    def remote_callback(self, event_name, data, kwargs):
        self.log(f"{inspect.currentframe().f_code.co_name} from {event_name}:{data}")
        event_type = data['new_state']['attributes'].get('event_type', None)

        if event_type is None:
            self.log(f"Warning: 'event_type' not found in {data['new_state']['attributes']}", level="WARNING")
            return  # Exit early to prevent further errors

        entity_id = data['entity_id']

        if event_type == "brightness_up_click":
            self.log("brightness_up_click")

            for light in self.__lights:
                self.turn_on(entity_id=light, brightness_step_pct="+10")
        elif event_type == "brightness_up_hold":
            self.log("brightness_up_hold")

            for light in self.__lights:
                self.turn_on(entity_id=light, brightness_pct="100")
        elif event_type == "brightness_down_click":
            self.log("brightness_down_click")

            for light in self.__lights:
                self.turn_on(entity_id=light, brightness_step_pct="-10")
        elif event_type == "brightness_down_hold":
            self.log("brightness_down_hold")

            for light in self.__lights:
                self.turn_on(entity_id=light, brightness_pct="10")
        elif event_type == "arrow_left_click":
            self.log("arrow_left_click")
            for light in self.__lights_left:
                self.toggle(light)
        elif event_type == "arrow_left_hold":
            self.log("arrow_left_hold")

            for light in self.__lights:
                self.turn_on(entity_id=light, color_temp_kelvin=self.get_state(light, attribute = "min_color_temp_kelvin"))
        elif event_type == "arrow_right_click":
            self.log("arrow_right_click")
            for light in self.__lights_right:
                self.toggle(light)
        elif event_type == "arrow_right_hold":
            self.log("arrow_right_hold")

            for light in self.__lights:
                self.turn_on(entity_id=light, color_temp_kelvin=self.get_state(light, attribute = "max_color_temp_kelvin"))
        elif event_type == "toggle":
            self.log("toggle")
            for light in self.__lights:
                self.toggle(light)
        else:
            self.log("Ignoring event")


