# coding=utf-8
from __future__ import absolute_import

# (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin

from .printercontrol import PrinterControl
from datetime import datetime
from .printjob import PrintJob, PrintJobTooEarly


class AutoprintPlugin(octoprint.plugin.StartupPlugin,
                      octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.AssetPlugin,
                      octoprint.plugin.TemplatePlugin,
                      octoprint.plugin.SimpleApiPlugin
                      ):

    def __init__(self) -> None:
        super().__init__()
        self._printJob = None

    # ~~ Startup Plugin

    def on_after_startup(self):
        self._printerControl = PrinterControl(self._logger, self._printer)
        self.assignSettings()

    # ~  TemplatePlugin mixin
    def get_template_configs(self):
        return [{
            "type": "settings",
            "custom_bindings": True
        },
            {
            "type": "tab",
            "custom_bindings": True
        }
        ]

    def get_template_vars(self):
        result = dict(
            state=dict(
                printer=self._printerControl.isPrinterOn,
                light=self._printerControl.isLightOn
            )
        )

        self._logger.info(result)
        return result

    # ~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return {
            "gpio": {
                "printer": 17,
                "light": 18
            },
            "printer": {
                "startupTime": 5
            },
            "nozzle": {
                "cooldownTemp": 60
            },
            "folders": {
                "autoprint": ''
            }
        }

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.assignSettings()

    def assignSettings(self):
        self._printerControl.printerGpio = self._settings.get(
            ["gpio", "printer"])
        self._printerControl.lightGpio = self._settings.get(["gpio", "light"])
        self._printerControl.startupTime = self._settings.get(
            ["printer", "startupTime"])
        self._printerControl.cooldownTemp = self._settings.get(
            ["nozzle", "cooldownTemp"])
        self._printerControl.autoprintFolder = self._settings.get(
            ["folders", "autoprint"])

    # ~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/autoprint.js"],
            "css": ["css/autoprint.css"],
            "less": ["less/autoprint.less"]
        }

    # ~~ SimpleApiPlugin mixin

    def get_api_commands(self):
        return {
            "startUpPrinter": [],
            "shutDownPrinter": [],
            "cancelShutDown" : [],
            "printWaiting": [],
            "toggleLight": [],
            "scheduleJob": [
                "file", "time", "startFinish", "turnOffAfterPrint"
            ]
        }

    def on_api_command(self, command, data):
        if "startUpPrinter" == command:
            self._printerControl.startUpPrinter()
        elif "shutDownPrinter" == command:
            self._printerControl.shutDownPrinter()
        elif "cancelShutDown" == command:
            self._printerControl.cancelShutDown()
        elif "toggleLight" == command:
            self._printerControl.toggleLight()
        elif "scheduleJob" == command:
            return self._handleScheduleJob(data)

    def on_api_get(self, request):
        result = {
            'state': {
                'printer': self._printerControl.isPrinterOn,
                'light': self._printerControl.isLightOn,
                'cooldown' : self._printerControl.isCoolingDown
            }
        }

        if None != self._printJob:
            result['scheduledJob'] = self._printJob.__dict__()

        return result

    def _handleScheduleJob(self, jobData):
        from flask import make_response
        time = datetime.fromtimestamp(jobData["time"]/1000)
        errors = []

        if not jobData["file"]:
            errors.append({
                'msg': "Please provide a gcode file for the scheduled print job!",
                'parameter': "file"
            })
        else:
            path = f'{self._printerControl.autoprintFolder}/{jobData["file"]}'
            try:
                pj = PrintJob(path,
                              time, jobData["turnOffAfterPrint"],
                              jobData["startFinish"],
                              self._logger,
                              self._file_manager)
                self._printJob = pj

            except PrintJobTooEarly as e:
                errors.append({
                    'msg': e.message,
                    'parameter': 'time'
                })

        if len(errors) > 0:
            return make_response({"errors": errors}, 400)
        else:
            return make_response(self._printJob.__dict__(), 200)

    # ~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "autoprint": {
                "displayName": "Autoprint Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "chof747",
                "repo": "octoprint-autoprint",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/chof747/octoprint-autoprint/archive/{target_version}.zip",
            }
        }


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Autoprint Plugin"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = AutoprintPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
