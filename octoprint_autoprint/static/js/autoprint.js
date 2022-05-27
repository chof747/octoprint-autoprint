/*
 * View model for OctoPrint-Autoprint
 *
 * Author: Christian Hofbauer
 * License: AGPLv3
 */

$(function() {
    function AutoprintViewModel(parameters) {
        var self = this;
        self.setttings = parameters[0];        
        self.state = ko.observable();


        // TODO: Implement your plugin's view model here.

        self.onBeforeBinding = function() {
            self.state({
                printer : plugin_autoprint_state.printer
            })
            console.log(self.settings);
        };

        self.startUpPrinter = function () {
            OctoPrint.simpleApiCommand("autoprint", "startUpPrinter", {}).then(function () {
                //self.updateGpioButtons();
            });
        };

        self.shutDownPrinter = function () {
            OctoPrint.simpleApiCommand("autoprint", "shutDownPrinter", {}).then(function () {
                //self.updateGpioButtons();
            });
        };

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
        elements: [ "#sidebar_plugin_autoprint" ]
    });
});
