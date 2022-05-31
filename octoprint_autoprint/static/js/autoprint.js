/*
 * View model for OctoPrint-Autoprint
 *
 * Author: Christian Hofbauer
 * License: AGPLv3
 */

$(function() {
    function AutoprintViewModel(parameters) {
        var self = this;
        self.settings = parameters[0];        
        self.statePrinter = ko.observable(false);
        self.stateLight = ko.observable(false);


        // TODO: Implement your plugin's view model here.

        self.onBeforeBinding = function() {
            console.log(self.settings);
            self.updateState();
        };

        self.startUpPrinter = function () {
            OctoPrint.simpleApiCommand("autoprint", "startUpPrinter", {}).then(function () {
                self.updateState();
            });
        };

        self.shutDownPrinter = function () {
            OctoPrint.simpleApiCommand("autoprint", "shutDownPrinter", {}).then(function () {
                self.updateState();
            });
        };

        self.toggleLight = function() {
            OctoPrint.simpleApiCommand("autoprint", "toggleLight", {}).then(function() {
                self.updateState();
            });
        }

        self.updateState = function () {
            OctoPrint.simpleApiGet("autoprint").then(function(printer_state) {
                self.statePrinter(printer_state.printer);
                self.stateLight(printer_state.light);
            });
        }

    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: AutoprintViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ "settingsViewModel" ],
        // Elements to bind to, e.g. #settings_plugin_autoprint, #tab_plugin_autoprint, ...
        elements: [ "#tab_plugin_autoprint" ]
    });
});
