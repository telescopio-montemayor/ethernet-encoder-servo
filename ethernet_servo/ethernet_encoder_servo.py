#!/usr/bin/env python

import eventlet
# cpppo uses blocking network calls, so we need this in order to play nice with flask-socketio
eventlet.monkey_patch()     # noqa

import json
import logging
import argparse
from datetime import datetime


from flask import Flask, render_template, g
from flask.json import jsonify
from flask_socketio import SocketIO

import serial
from cpppo.server.enip.get_attribute import proxy_simple
from cpppo.server.enip import poll

from . import api
from .control import devices

log = logging.getLogger('ethernet-encoder-servo')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
api.register(app)

socketio = SocketIO(app)

POSITION_PARAM = '@0x23/1/0x0a'
VELOCITY_PARAM = '@0x23/1/0x18'
VELOCITY_QUERY = [('@0x23/1/0x18', 'DINT')]
POSITION_VELOCITY_QUERY = [('@0x23/1/0x0a', 'DINT')]


def failure(exc):
    log.error(exc)


def build_process_function(device):

    def _process(par, val):
        now = datetime.now()
        now_formatted = now.isoformat()
        parameter = {
            POSITION_PARAM: 'position',
            VELOCITY_PARAM: 'velocity',
        }[par[0]]

        if parameter is not 'position':
            return

        value = val[0]

        controller = device.controller
        state = controller.state
        controller.update(value)

        state.update({
            'estimated_speed': state['speed_cps'],
            'id': device.id,
            'name': device.name,
            'host': device.host,
            'port': device.port,
            'interval': device.interval,
            'dt': state['dt'],
            'steps': device.steps,
            'offset': device.offset,
            'value': state['position'],
            'raw_value': value,
            'control_out': state['speed_cps'],
            'timestamp': now_formatted,
            'target_angle': state['target_angle'].to_dict(),
            'target_astronomical': state['target_astronomical'].to_dict(),
            'position_angle': state['position_angle'].to_dict(),
            'position_astronomical': state['position_astronomical'].to_dict(),
        })
        socketio.emit(parameter, state, broadcast=True)

    return _process


def build_polling_task(device):
    poller = socketio.start_background_task(
        target=poll.poll,
        proxy_class=proxy_simple,
        address=(device.host, device.port),
        cycle=device.interval / 1000,
        timeout=0.5,
        process=build_process_function(device),
        failure=failure,
        params=POSITION_VELOCITY_QUERY,
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


@socketio.on('get_control_state')
def ws_get_control_state():
    return devices.get()[0].controller.state


@socketio.on('set_control_state')
def ws_set_control_state(new_state):
    pid_controller = devices.get()[0].controller.pid_controller

    Kp = new_state.get('Kp', None)
    Ki = new_state.get('Ki', None)
    Kd = new_state.get('Kd', None)
    alpha = new_state.get('alpha', None)
    setpoint = new_state.get('setpoint', None)

    if Kp is not None:
        pid_controller.Kp = Kp

    if Ki is not None:
        pid_controller.Ki = Ki

    if Kd is not None:
        pid_controller.Kd = Kd

    if alpha is not None:
        pid_controller.derivative_filter.alpha = alpha

    if setpoint is not None:
        pid_controller.SetPoint = setpoint


def main():
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    pollers = []

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug',
                        required=False,
                        action='store_true',
                        help='Shows debug messages')

    parser.add_argument('--dry-run',
                        required=False,
                        action='store_true',
                        help='Do not connect to the encoders or controllers')

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

    parser.add_argument('--serial',
                        type=str,
                        default='/dev/ttyACM0',
                        help='Serial port to use for speed control (/dev/ttyUSB0)')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()

    with open(args.config, 'r') as config_file:
        config = json.load(config_file)
        for idx, device_config in enumerate(config.get('devices', [])):
            device = devices.create(**device_config)

            if not args.dry_run:
                serial_port = serial.Serial(args.serial, baudrate=57600)
                serial_port.write_timeout = 0.05
                serial_port.read_timeout = 0.05
                device.serial_port = serial_port

    if not args.dry_run:
        for device in devices.get():
            log.info('Starting polling task for: %s', device)
            poller = build_polling_task(device)
            pollers.append(poller)

    # reloader launchs another thread for the main process and that means two instances of the controller and encoder poller but only one of them is managed by the UI. Fun times.
    socketio.run(app, host=args.host, port=args.port, use_reloader=False, debug=True)
