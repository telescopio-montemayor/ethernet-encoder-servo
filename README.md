# Ethernet Encoder Servo

Networked servo controller around CIP encoders and step/direction motors for use with a telescope.
This project is developed around Allen Bradley 842E absolute encoders but should work with others.

## Installation

Under a virtualenv do:

```
    pip install -e .
```

in order to fetch all the dependencies and install it as *ethernet-servo*

## Running:

Copy the file *config_sample.json* to config.json and edit as needed.

```js
{
    "devices": [
        // One of more of the following:
        {
            "name": "Simulated device",   // Verbose name to display in user interfaces.
            "id": "some unique name",     // Device id, defaults to *name* if not given.
            "host": "localhost",          // mandatory, host or ip address of the ethernet encoder
            "port": 44818,                // optional, defaults to 44818
            "interval": 1000,             // Polling interval in milliseconds. Optional. Defaults to 50 milliseconds
            "steps": 25600,               // Steps per revolution of the stepper driver, defaults to 25600.
            "offset": 0,                  // Position offset in raw encoder counts, defaults to 0.
            "gear_ratio_num": 1,          // If this motor is geared, this is the output/input ratio.
            "gear_ratio_den": 256,        //
            "axis": "B",                  // Axis on the step/direction usb interface.
            "invert": false,              // Flips the direction of increasing angle.
            "max_speed": 20000,           // Maximum speed in steps per second.
            "supports_hour_angle": true,  // If this axis can be positioned in hour angle units.
            "can_track": true,            // If this axis can track a target with constant speed.
            "Kp": 1,                      // Proportional gain. Optional.
            "Ki": 1,                      // Integral gain. Optional.
            "Kd": 1,                      // Derivative gain. Optional.
            "derivative_filtering": .75   // Derivative error low pass filtering. Float between 0 and 1.
        }
    ]
}
```

Then run:

```
    ethernet-servo --config config.json
```

To start the server listening on http://localhost:5000. Go to http://localhost:5000/api to explore the available
commands.

The full set of options is:

```
$ ethernet-servo --help
usage: ethernet-servo [-h] [--debug] [--dry-run] [--host HOST] [--port PORT]
                      --config CONFIG [--state-store-path STATE_STORE_PATH]
                      [--state-save-interval STATE_SAVE_INTERVAL]
                      [--serial SERIAL]

optional arguments:
  -h, --help            show this help message and exit
  --debug               Shows debug messages
  --dry-run             Do not connect to the encoders or controllers
  --host HOST           The hostname or IP address for the server to listen
                        on. Defaults to 127.0.0.1
  --port PORT           The port number for the server to listen on. Defaults
                        to 5000
  --config CONFIG       Path to the configuration JSON file
  --state-store-path STATE_STORE_PATH
                        Path to load and save encoder status (JSON)
  --state-save-interval STATE_SAVE_INTERVAL
                        Interval in milliseconds between state saving.
                        Defaults to 1000
  --serial SERIAL       Serial port to use for speed control (/dev/ttyACM0
```


## Motor control protocol

The control message format is:

```
\n[AXIS][SPEED]\n
```

Where *AXIS* is one of A, B... etc. (uppercase) and speed is the desired steps per second for that axis as a signed
value.
For example:

```
\nA12345\n
```
