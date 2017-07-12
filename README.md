# Ethernet Encoder Server

Just a small server to expose ethernet encoders using the Common Industrial Protocol via SocketIO and REST.

## Installation

Under a virtualenv do:

```
    pip install -r requirements.txt
```

in order to fetch all the dependencies.

## Running:

Copy the file *config_sample.json* to config.json and edit as needed.

```js
{
    "devices": [
        // One of more of the following:
        {
            "host": "localhost",        // mandatory
            "port": 44818,              // optional, defaults to 44818
            "interval": 1000,           // Polling interval in milliseconds. Optional. Uses the --interval argument if passed.
                                        // Otherwise defaults to 1000 (1 second)
            "steps": 262144,            // Steps per revolution, defaults to 262144.
            "offset": 0,                // Position offset, defaults to 0.
            "name": "Simulated device"  // Name to display. Optional. Defaults to 'position host:port'.
        }
    ]
}
```

Then run:

```
    ./ethernet_encoder_server.py --config config.json
```

To start the server listening on http://localhost:5000. Besides that page and websocket events there's also the route
*/devices* listing all the configured devices and their last position.

The full set of options is:
```
    ./ethernet_encoder_server.py --help
    usage: ethernet_encoder_server.py [-h] [--debug] [--host HOST] [--port PORT]
                                      --config CONFIG [--interval INTERVAL]

    optional arguments:
      -h, --help           show this help message and exit
      --debug              Shows debug messages
      --host HOST          The hostname or IP address for the server to listen on.
                           Defaults to 127.0.0.1
      --port PORT          The port number for the server to listen on. Defaults
                           to 5000
      --config CONFIG      Path to the configuration JSON file
      --interval INTERVAL  Default polling interval in milliseconds
```


