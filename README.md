# OctoPrint-Autoprint

The octoprint autoprint plugin has the following functionalities:

1. Enable the remote powering on/off of a printer and a light above the printer via two distinct
   GPIO pins (which are most likely connected to relais) - also exposing these GPIOs
2. Automatically disconnect and turn off the printer after a print is finished - with the option
   to wait for a proper cool down
3. Start the printer and begin printing a specific file either at a given time or at a time
   so that the print will be finished as specified 

See the details on the [design and concept in Concept.md](Concept.md) 

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/chof747/octoprint-autoprint/archive/master.zip

and use `pip install .`to install the plugin

## Setup of a development environment

1. Setup an OctoPrint development environment as described in the tutorial
   https://docs.octoprint.org/en/master/plugins/gettingstarted.html
   **NOTE:** If you are doing this in a separate path you can use this one for all your 
   plugin development 

2. Create your plugin directory and initiate your plugin as described in the tutorial. 
   Always start the virtual environment created for the OctoPrint dev environment when dealing with the plugin developmen.
   I.e. instead of
   ```sh
   source ./venv/bin/activate
   ```
   use 
   ```sh
   source <Directory of your OctoPrint DevEnv>/venv/bin/activate
   ```
   On the first setup outside of a raspberry pi please also install the RPi.GPIO simulation library in the virtual environment:
   ```sh
   pip install git+https://github.com/nosix/raspberry-gpio-emulator/
   ```

3. Start octoprint always from your plugin directory (in the virtual environment as described    in  2) with:
   ```sh 
   tests/octoprint_dev.sh
   ```

## Configuration

**TODO:** Describe your plugin's configuration options (if any).
