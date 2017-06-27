#!/usr/bin/env python

import eventlet
# cpppo uses blocking network calls, so we need this in order to play nice with flask-socketio
eventlet.monkey_patch()     # noqa

import json
import logging
import argparse
from datetime import datetime


from flask import Flask, render_template
from flask.json import jsonify
from flask_socketio import SocketIO

from cpppo.server.enip.get_attribute import proxy_simple
from cpppo.server.enip import poll

log = logging.getLogger('ethernet-encoder-server')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

POSITION_QUERY = [('@0x23/1/0x0a', 'DINT')]


# Filled later from config.
devices = []
devices_by_id = {}


def failure(exc):
    log.error(exc)


def build_process_function(device):
    def _process(par, val):
        now = datetime.now().isoformat()
        position = val[0]
        socketio.emit('position', {
            'name': device['name'],
            'host': device['host'],
            'port': device['port'],
            'id': device['id'],
            'position': position,
            'timestamp': now,
        }, broadcast=True)
        devices_by_id[device['id']]['position'] = position
        devices_by_id[device['id']]['timestamp'] = now
    return _process


def build_polling_task(device):
    poller = socketio.start_background_task(
        target=poll.poll,
        proxy_class=proxy_simple,
        address=(device['host'], device['port']),
        cycle=device['interval'] / 1000,
        timeout=0.5,
        process=build_process_function(device),
        failure=failure,
        params=POSITION_QUERY,
    )
    return poller


def process(par, val):
    socketio.emit('position', {
        'value': val,
        'time': datetime.now().isoformat(),
    }, broadcast=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/devices')
def list_devices():
    return jsonify(devices)


if __name__ == '__main__':
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    pollers = []

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug',
                        required=False,
                        action='store_true',
                        help='Shows debug messages')

    parser.add_argument('--host',
                        required=False,
                        default='127.0.0.1',
                        help='The hostname or IP address for the server to listen on. Defaults to 127.0.0.1')

    parser.add_argument('--port',
                        required=False,
                        default=5000,
                        type=int,
                        help='The port number for the server to listen on. Defaults to 5000')

    parser.add_argument('--config',
                        required=True,
                        help='Path to the configuration JSON file')

    parser.add_argument('--interval',
                        type=int,
                        default=1000,
                        help='Default polling interval in milliseconds')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()

    default_interval = args.interval

    with open(args.config, 'r') as config_file:
        config = json.load(config_file)
        for idx, device in enumerate(config.get('devices', [])):
            device.setdefault('port', 44818)
            device.setdefault('interval', default_interval)
            device_id = '{} {}:{}'.format(idx, device['host'], device['port'])
            device['id'] = device_id
            device.setdefault('name', device_id)
            devices.append(device)
            devices_by_id[device_id] = device

    for device in devices:
        log.info('Starting polling task for: %s', device)
        poller = build_polling_task(device)
        pollers.append(poller)

    socketio.run(app, host=args.host, port=args.port, use_reloader=True)
