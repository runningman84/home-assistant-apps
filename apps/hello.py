"""HelloWorld app: simple example app that logs startup messages.

Main features:
- Minimal example that demonstrates the AppDaemon lifecycle and logging.

This file is intentionally simple and used as a template for new apps.

See module docstring and inline examples for usage.
"""

import appdaemon.plugins.hass.hassapi as hass


class HelloWorld(hass.Hass):

  def initialize(self):
     self.log("Hello from AppDaemon")
     self.log("You are now ready to run Apps!")
