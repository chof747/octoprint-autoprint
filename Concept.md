Autoprint plugin design concept
===============================

# Requirements

## Use Cases

1. Enable the remote powering on/off of a printer and a light above the printer via two distinct
   GPIO pins (which are most likely connected to relais) - also exposing these GPIOs
2. Automatically disconnect and turn off the printer after a print is finished - with the option
   to wait for a proper cool down
3. Start the printer and begin printing a specific file either at a given time or at a time
   so that the print will be finished as specified 

## Detailed considerations

- The GPIO pins must be configurable in order to change the HW design
- The cooldown nozzle temperature which allows shutdown of printer must be configurable
- Always disconnect the printer (if connected) before it is turned off
- Cross check if a printer turn off is requested while printing (either via let the user reconfirm his decision or via a special emergency shut down as an escalation level)

# Solution

The plugin will provide different approaches for the use cases:

1. Printer and Light power switch buttons will be enabled on the UI where the user can directly 
   turn on and off the light and printer
2. Before or while a print is running a flag (on the same place as the power switch buttons)
   will be available to trigger or untrigger the shutdown after completion
3. If the printer is not printing the user can load any printing file (not starting the print)
   and request via the GUI a scheduled start for the job (either with a specified start or end
   time - based on the loaded printer job

## Data Model and Settings

The plugin requires no real data model just the following values should be stored

### Settings

- `gpio.light` ... the GPIO pin which triggers the light/light relaiss
- `gpio.printer` ... the GPIO pin which triggers the power of the printer
- `nozzle.cooldown_temp` ... the temperature to which the nozzle must cool down in order to be
  able to turn off the printer

### Controll Data (not persisted)

- `shutdownWhenFinished`... boolean value indicating if the plugin should shutdown the printer
  when the print has been finished and the nozzle has cooled down sufficiently
- `printStartTime` ... set or calculated start time for the printer based on the info provided
  by the user

