import appdaemon.plugins.hass.hassapi as hass

# {
#     "event_type": "folder_watcher",
#     "data": {
#         "event_type": "modified",
#         "path": "/tmp/camera_doods_flur_unten_20190908_223303.jpg",
#         "file": "camera_doods_flur_unten_20190908_223303.jpg",
#         "folder": "/tmp"
#     },
#     "origin": "LOCAL",
#     "time_fired": "2019-09-08T20:33:04.273143+00:00",
#     "context": {
#         "id": "7f43b291edba4b7cb818bd6c11fc937d",
#         "parent_id": null,
#         "user_id": null
#     }
# }

class TelegramBotEventListener(hass.Hass):
    """Event listener for Telegram bot events."""

    def initialize(self):
        """Configure defaults"""
        self._alarm_control_panel = self.args.get("alarm_control_panel", "alarm_control_panel.ha_alarm")
        self._guest_control = self.args.get("guest_control", None)
        self._alarm_pin = self.args.get("alarm_pin", None)
        self._user_ids = self.args.get("user_ids",[])

        """Listen to Telegram Bot events of interest."""
        #self.listen_event(self.receive_telegram_text, 'telegram_text')
        #self.listen_event(self.receive_telegram_callback, 'telegram_callback')
        #self.listen_event(self.receive_telegram_command, 'telegram_command')
        # Alarm Control
        self.listen_event(self.receive_telegram_command_alarm_status, 'telegram_command', command = '/alarm_status')
        self.listen_event(self.receive_telegram_callback_alarm, 'telegram_callback', data = '/alarm_arm_away')
        self.listen_event(self.receive_telegram_callback_alarm, 'telegram_callback', data = '/alarm_arm_home')
        self.listen_event(self.receive_telegram_callback_alarm, 'telegram_callback', data = '/alarm_trigger')
        self.listen_event(self.receive_telegram_callback_alarm, 'telegram_callback', data = '/alarm_disarm')
        self.listen_event(self.receive_telegram_callback_alarm, 'telegram_callback', data = '/alarm_picture')
        self.listen_state(self.alarm_state_changed_callback,
                          self._alarm_control_panel, new="triggered")
        self.listen_state(self.alarm_state_changed_callback,
                          self._alarm_control_panel, old="armed_home", new="pending")
        self.listen_state(self.alarm_state_changed_callback,
                          self._alarm_control_panel, old="armed_away", new="pending")
        self.listen_state(self.alarm_state_changed_callback,
                          self._alarm_control_panel, old="disarmed", new="pending")
        self.listen_state(self.alarm_state_changed_callback,
                          self._alarm_control_panel, new="disarmed")
        self.listen_state(self.alarm_state_changed_callback,
                          self._alarm_control_panel, new="armed_away")
        self.listen_state(self.alarm_state_changed_callback,
                          self._alarm_control_panel, new="armed_home")
        # Guest Control
        #self.listen_event(self.receive_telegram_command_guest, 'telegram_command', command = '/guest_status')
        #self.listen_event(self.receive_telegram_command_guest, 'telegram_command', command = '/guest_enable')
        #self.listen_event(self.receive_telegram_command_guest, 'telegram_command', command = '/guest_disable')
        #self.listen_event(self.receive_telegram_command_guest, 'telegram_command', command = '/guest_on')
        #self.listen_event(self.receive_telegram_command_guest, 'telegram_command', command = '/guest_off')
        #self.listen_event(self.receive_telegram_callback_guest, 'telegram_callback', data = '/guest_enable')
        #self.listen_event(self.receive_telegram_callback_guest, 'telegram_callback', data = '/guest_disable')


    def receive_telegram_command(self, event_id, payload_event, *args):
        """Event listener for Telegram callback queries."""
        assert event_id == 'telegram_command'
        user_id = payload_event['user_id']
        chat_id = payload_event['chat_id']

        self.log("Got command {}".format(payload_event))

    def alarm_state_changed_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            "Callback alarm_state_changed_callback from {}:{} {}->{}".format(entity, attribute, old, new))

        msg = "Alarm state changed from {} to {}".format(old, new).replace('_', ' ')
        disable_notification = True

        if new == 'triggered':
            disable_notification = False
        if new == 'pending' and ( old == 'armed_home' or old == 'armed_away'):
            disable_notification = False

        if(self.get_state(self._alarm_control_panel) == 'disarmed'):
            keyboard = [[("Arm alarm home", "/alarm_arm_home"),
                        ("Arm alarm away", "/alarm_arm_away")]]
        elif(self.get_state(self._alarm_control_panel) == 'triggered'):
            keyboard = [[("Disarm alarm", "/alarm_disarm"),
                        ("Get picture", "/alarm_picture")]]
        else:
            keyboard = [[("Disarm alarm", "/alarm_disarm"),
                        ("Trigger alarm", "/alarm_trigger")]]

        for user_id in self._user_ids:
            self.log("Sending message {} to user_id {}".format(msg, user_id))
            self.call_service('telegram_bot/send_message',
                                service_data={
                                    "title" : '*Alarm Control*',
                                    "target" : user_id,
                                    "message" : msg,
                                    "inline_keyboard" : keyboard,
                                    "disable_notification" : disable_notification
                                })

    def receive_telegram_callback_alarm(self, event_id, payload_event, *args):
        """Event listener for Telegram callback queries."""
        assert event_id == 'telegram_callback'
        data_callback = payload_event['data']
        callback_id = payload_event['id']
        user_id = payload_event['user_id']
        title = '*Alarm Control*'

        self.log("Got callback {}".format(payload_event))

        if data_callback == '/alarm_arm_home':  # Message editor:
            self.call_service("alarm_control_panel/alarm_arm_home",
                              entity_id=self._alarm_control_panel, code=self._alarm_pin)

            # Answer callback query
            self.call_service('telegram_bot/answer_callback_query',
                                service_data={
                                    "message" : 'Alarm armed home!',
                                    "callback_query_id" : callback_id,
                                    "show_alert" : True
                                })

            # Edit the message origin of the callback query
            msg_id = payload_event['message']['message_id']
            user = payload_event['from_first']
            msg = "Alarm mode is {}".format(self.get_state(self._alarm_control_panel)).replace('_', ' ')
            self.call_service('telegram_bot/edit_message',
                                service_data={
                                    "chat_id" : chat_id,
                                    "message_id" : message_id,
                                    "title" : title,
                                    "message" : msg
                                })
        elif data_callback == '/alarm_arm_away':  # Message editor:
            self.call_service("alarm_control_panel/alarm_arm_away",
                              entity_id=self._alarm_control_panel, code=self._alarm_pin)

            # Answer callback query
            self.call_service('telegram_bot/answer_callback_query',
                                service_data={
                                    "message" : 'Alarm armed away!',
                                    "callback_query_id" : callback_id,
                                    "show_alert" : True
                                })

            # Edit the message origin of the callback query
            msg_id = payload_event['message']['message_id']
            user = payload_event['from_first']
            msg = "Alarm mode is {}".format(self.get_state(self._alarm_control_panel)).replace('_', ' ')
            self.call_service('telegram_bot/edit_message',
                                service_data={
                                    "chat_id" : chat_id,
                                    "message_id" : message_id,
                                    "title" : title,
                                    "message" : msg
                                })
        elif data_callback == '/alarm_disarm':  # Message editor:
            self.call_service("alarm_control_panel/alarm_disarm",
                              entity_id=self._alarm_control_panel, code=self._alarm_pin)

            # Answer callback query
            self.call_service('telegram_bot/answer_callback_query',
                              message='Alarm disarmed!',
                              callback_query_id=callback_id,
                              show_alert=True)

            # Edit the message origin of the callback query
            msg_id = payload_event['message']['message_id']
            user = payload_event['from_first']
            msg = "Alarm mode is {}".format(self.get_state(self._alarm_control_panel)).replace('_', ' ')
            self.call_service('telegram_bot/edit_message',
                                service_data={
                                    "chat_id" : chat_id,
                                    "message_id" : message_id,
                                    "title" : title,
                                    "message" : msg
                                })
                              #inline_keyboard=keyboard)



    # def receive_telegram_command_guest(self, event_id, payload_event, *args):
    #     """Event listener for Telegram callback queries."""
    #     assert event_id == 'telegram_command'
    #     #assert self._alarm_control_panel is not None
    #     user_id = payload_event['user_id']
    #     chat_id = payload_event['chat_id']

    #     self.log("Got command {}".format(payload_event))

    #     keyboard = None
    #     if payload_event['command'] == '/guest_enable':
    #         self.turn_on(self._guest_control)
    #         msg = "Guest mode enabled"
    #     elif payload_event['command'] == '/guest_on':
    #         self.turn_on(self._guest_control)
    #         msg = "Guest mode enabled"
    #     elif payload_event['command'] == '/guest_disable':
    #         self.turn_off(self._guest_control)
    #         msg = "Guest mode disabled"
    #     elif payload_event['command'] == '/guest_off':
    #         self.turn_off(self._guest_control)
    #         msg = "Guest mode disabled"
    #     elif payload_event['command'] == '/guest_status':
    #         if(self.get_state(self._guest_control ) == 'on'):
    #             keyboard = [[("Disable guest mode", "/guest_disable")]]
    #         else:
    #             keyboard = [[("Enable guest mode", "/guest_enable")]]
    #         msg = "Guest mode is {}".format(self.get_state(self._guest_control))

    #     self.call_service('telegram_bot/send_message',
    #                         service_data={
    #                             "title" : '*Guest Control*',
    #                             "target" : user_id,
    #                             "message" : msg,
    #                             "inline_keyboard" : keyboard,
    #                             "disable_notification" : True
    #                         })


    # def receive_telegram_callback_guest(self, event_id, payload_event, *args):
    #     """Event listener for Telegram callback queries."""
    #     assert event_id == 'telegram_callback'
    #     data_callback = payload_event['data']
    #     callback_id = payload_event['id']
    #     user_id = payload_event['user_id']

    #     self.log("Got callback {}".format(payload_event))

    #     if data_callback == '/guest_enable':  # Message editor:
    #         self.turn_on(self._guest_control)

    #         # Answer callback query
    #         self.call_service('telegram_bot/answer_callback_query',
    #                           message='Guest Mode enabled!',
    #                           callback_query_id=callback_id,
    #                           show_alert=True)

    #         # Edit the message origin of the callback query
    #         msg_id = payload_event['message']['message_id']
    #         user = payload_event['from_first']
    #         title = '*Guest Control*'
    #         msg = "Guest mode is {}".format(self.get_state(self._guest_control))
    #         self.call_service('telegram_bot/edit_message',
    #                           chat_id=user_id,
    #                           message_id=msg_id,
    #                           title=title,
    #                           message=msg)
    #     elif data_callback == '/guest_disable':  # Message editor:
    #         self.turn_off(self._guest_control)

    #         # Answer callback query
    #         self.call_service('telegram_bot/answer_callback_query',
    #                           message='Guest Mode disabled!',
    #                           callback_query_id=callback_id,
    #                           show_alert=True)

    #         # Edit the message origin of the callback query
    #         msg_id = payload_event['message']['message_id']
    #         user = payload_event['from_first']
    #         title = '*Guest Control*'
    #         msg = "Guest mode is {}".format(self.get_state(self._guest_control))
    #         self.call_service('telegram_bot/edit_message',
    #                           chat_id=user_id,
    #                           message_id=msg_id,
    #                           title=title,
    #                           message=msg)
    #                           #inline_keyboard=keyboard)


    def receive_telegram_command_alarm_status(self, event_id, payload_event, *args):
        """Event listener for Telegram callback queries."""
        assert event_id == 'telegram_command'
        #assert self._alarm_control_panel is not None
        user_id = payload_event['user_id']
        chat_id = payload_event['chat_id']

        if(self.get_state(self._alarm_control_panel) == 'disarmed'):
            keyboard = [[("Arm alarm home", "/alarm_arm_home"),
                        ("Arm alarm away", "/alarm_arm_away")]]
        elif(self.get_state(self._alarm_control_panel) == 'triggered'):
            keyboard = [[("Disarm alarm", "/alarm_disarm"),
                        ("Get picture", "/alarm_picture")]]
        else:
            keyboard = [[("Disarm alarm", "/alarm_disarm"),
                        ("Trigger alarm", "/alarm_trigger")]]

        msg = "Alarm status is {}".format(self.get_state(self._alarm_control_panel))

        self.call_service('telegram_bot/send_message',
                            service_data={
                                "title" : '*Alarm System*',
                                "target" : user_id,
                                "message" : msg,
                                "inline_keyboard" : keyboard,
                                "disable_notification" : True
                            })
