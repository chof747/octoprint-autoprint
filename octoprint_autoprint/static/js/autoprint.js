/*
* View model for OctoPrint-Autoprint
*
* Author: Christian Hofbauer
* License: AGPLv3
*/

$(function () {

    function AutoprintViewModel(parameters) {

        /* 
        * Data and Observables **********************************************************
        */

        var self = this;
        self.settings = parameters[0];
        self.filesViewModel = parameters[1];
        self.interval = undefined;
        self.state = {
            printer: ko.observable(false),
            light: ko.observable(false),
            cooldown: ko.observable(false),
            connected: ko.observable(false),
            printInProgress: ko.observable(false)
        };

        self.list = {
            folder: ko.observableArray(),
            file: ko.observableArray()
        };
        self.autoprint = {
            turnOffAfterPrint: ko.observable(false),
            startFinish: ko.observable('start'),
            time: ko.observable((new Date()).getTime()),
            file: ko.observable(),
            folder: ko.observable('')
        };

        self.setFolder = ko.computed({
            read: function() {
                return "/" + this.autoprint.folder();
            },
            write: function(folder) {
                if ((folder) && ('/' == folder[0]))
                {
                    folder = folder.substring(1);
                }
    
                this.autoprint.folder(folder);
    
            },
            owner : self
        })


        self.errormsgs = {
            time: ko.observable(undefined),
            file: ko.observable(undefined)
        }

        self.scheduledJob = {
            file: ko.observable(undefined),
            startTime: ko.observable(undefined),
            turnOffAfterPrint: ko.observable(undefined)
        }

        self.timeDisplay = ko.computed({
            read: function () {
                var time = this.autoprint.time();
                var date = undefined;
                if (undefined == time) {
                    date = new Date();
                } else {
                    date = new Date(time);
                }
                date.setSeconds(0);
                date.setMilliseconds(0);
                return (new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString()).slice(0, -1)
            },
            write: function (val) {
                this.autoprint.time((new Date(val)).getTime());
            },
            owner: self
        });

        /* 
        * Eventhandlers *****************************************************************
        */

        self.onStartup = function () {
            self.updateFolderList();
        };

        self.onTabChange = function (next, current) {
            console.log(next, current);
            if ("#tab_plugin_autoprint" == next) {
                self.interval = window.setInterval(self.updateState, 500);
            } else if (undefined !== self.interval) {
                window.clearInterval(self.interval);
                self.interval = undefined;
            }
        };

        self.onBeforeBinding = function () {
            console.log(self.settings);
            ko.computed(self.updateFiles);
            self.updateState();
        };

        self.onEventFolderAdded = function () {
            self.updateFolderList();
        }

        self.onEventFolderRemoved = function () {
            self.updateFolderList();
        }

        self.onEventFolderMoved = function () {
            self.updateFolderList();
        }

        self.filesViewModel.selectFileFromBrowser = function(/* String */ path)
        {
            var tokens = path.split("/");
            var filename = tokens.pop();
            var pathname = tokens.join("/");

            self.autoprint.folder(pathname);
            if( def = self.updateFiles())
            {
                def.done(function() {
                    self.autoprint.file(filename);
                });
            }
            

        }

        /* 
        * Actions ***********************************************************************
        */

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

        self.cancelShutDown = function () {
            OctoPrint.simpleApiCommand("autoprint", "cancelShutDown", {}).then(function () {
                self.updateState();
            });
        }

        self.toggleLight = function () {
            OctoPrint.simpleApiCommand("autoprint", "toggleLight", {}).then(function () {
                self.updateState();
            });
        }

        self.scheduleJob = function () {
            job = {
                file: self.autoprint.file() || "",
                folder: self.autoprint.folder() || "",
                time: self.autoprint.time(),
                turnOffAfterPrint: self.autoprint.turnOffAfterPrint(),
                startFinish: self.autoprint.startFinish()
            }

            OctoPrint.simpleApiCommand("autoprint", "scheduleJob", job).then(
                self.handlePrintJobSuccess,
                self.handlePrintJobError);
        }

        self.cancelJob = function () {
            OctoPrint.simpleApiCommand("autoprint", "cancelJob").then(
                self.handlePrintJobSuccess
            );
        }

        /* 
        * Update Functions **************************************************************
        */


        self.updateState = function () {
            OctoPrint.simpleApiGet("autoprint").then(function (printer_state) {
                self.state.printer(printer_state.state.printer);
                self.state.light(printer_state.state.light);
                self.state.cooldown(printer_state.state.cooldown);
                self.state.connected(printer_state.state.connected);
                self.state.printInProgress(printer_state.state.printInProgress);

                if (undefined !== printer_state.scheduledJob) {
                    self.updateScheduledJob(printer_state.scheduledJob);
                }
            });
        }

        self.updateScheduledJob = function (jobdata) {
            if (undefined !== jobdata) {
                self.scheduledJob.file(jobdata.file);
                self.scheduledJob.startTime(jobdata.startTime);
                self.scheduledJob.turnOffAfterPrint(jobdata.turnOffAfter);    
            } else {
                self.scheduledJob.file(undefined)
            }
        }

        self.updateFolderList = function () {
            var result = [];

            var readFolder = function (folder) {
                _.each(_.filter(folder, function (entry) {
                    return entry.type == "folder";
                }), function (folder) {
                    result.push("/" + folder.path);
                    if (folder.children.length > 0) {
                        readFolder(folder.children.sort(sortFileList));
                    }
                });
            };

            var sortFileList = function (a, b) {
                return (a.name > b.name) ? 1 : ((a.name < b.name) ? -1 : 0);
            }

            OctoPrint.files.list(true).done(function (response) {
                readFolder(response.files.sort(sortFileList));
                result.unshift("/");
                self.list.folder(result);
            })
        }

        self.updateFiles = function () {
            var folder = self.autoprint.folder();
            var result = [];

            if (undefined !== folder) {
                var path = [ 'local' ];
                if (folder) {
                    path.push(folder)
                }

                return OctoPrint.files.listForLocation(path.join('/'), false).done(function (response) {
                    _.each(response.children, function (file) {
                        if (file.type == "machinecode") {
                            result.push(file.name);
                        }
                    })
                    _.each(response.files, function(file) {
                        if (file.type == "machinecode") {
                            result.push(file.name);
                        }
                    })

                    self.list.file(result);
                });
            }
            else
            {
                return null;
            }
        };

        /*
        * Response Hanlders ************************************************************* 
        */

        self.clearErrorMessages = function () {
            self.errormsgs.time(undefined);
            self.errormsgs.file(undefined);

        }

        self.handlePrintJobError = function (errors) {
            self.clearErrorMessages();
            errors.responseJSON.errors.forEach(e => {
                self.errormsgs[e.parameter](e.msg)
            });
        }

        self.handlePrintJobSuccess = function (data) {
            self.clearErrorMessages();
            self.updateScheduledJob(data);
        }


        $(document).ready(function() {
			let regex = /<div class="btn-group action-buttons">([\s\S]*)<.div>/mi;
			let template = '<div class="btn btn-mini" data-bind="click: function() { if ($root.loginState.isUser()) { $root.selectFileFromBrowser($data.path); } else { return; } }, css: {disabled: !$root.loginState.isUser()}" title="Select for auto printing"><i class="fa fa-calendar-o"></i></div>';

          
			$("#files_template_machinecode").text(function () {
				return $(this).text().replace(regex, '<div class="btn-group action-buttons">$1	' + template + '></div>');
			});
        });

    };

    /* view model class, parameters for constructor, container to bind to
    * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
    * and a full list of the available options.
    */
    OCTOPRINT_VIEWMODELS.push({
        construct: AutoprintViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: ["settingsViewModel", "filesViewModel"],
        // Elements to bind to, e.g. #settings_plugin_autoprint, #tab_plugin_autoprint, ...
        elements: ["#settings_plugin_autoprint", "#tab_plugin_autoprint"]
    });
});
