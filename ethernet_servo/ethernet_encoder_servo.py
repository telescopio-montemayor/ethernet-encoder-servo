#!/usr/bin/env python

## cpppo uses blocking network calls, so we need this in order to play nice with flask-socketio
import gevent
import gevent.monkey
gevent.monkey.patch_all() # noqa

import sys
import signal
import atexit

import json
import logging
import argparse
from datetime import datetime

import munch

from flask import Flask, render_template, g
from flask.json import jsonify
from flask_socketio import SocketIO

from cpppo.server.enip.get_attribute import proxy_simple
from cpppo.server.enip import poll

from . import api
from .control import devices, units, SerialPortInterface

log = logging.getLogger('ethernet-encoder-servo')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
api.register(app)

socketio = SocketIO(app, async_mode='gevent')

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


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('get_control_state')
def ws_get_control_state(device_id=None):
    if device_id is not None:
        try:
            return devices.get(device_id).controller.state
        except AttributeError:
            pass
    else:
        return [device.controller.state for device in devices.get()]


@socketio.on('set_control_state')
def ws_set_control_state(device_id, new_state):
    device = devices.get(device_id)

    if not device:
        return

    pid_controller = device.controller.pid_controller

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


def save_state(path, *args, **kwargs):
    all_state = {}
    for device in devices.get():
        state = device.controller.state
        for k, v in state.items():
            if v.__class__ in (units.AnglePosition, units.AstronomicalPosition):
                state[k] = v.to_dict()
        all_state[device.id] = state

    with open(path, 'w') as f:
        f.write(munch.munchify(all_state).toJSON(indent=4))


def load_state(path):
    contents = ''
    try:
        with open(path, 'r') as f:
            contents = f.read()

    except FileNotFoundError:
        return {}

    try:
        return json.loads(contents)
    except:
        return {}


def main():

    initial_state = {}
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

    parser.add_argument('--state-store-path', type=str, required=False, default='', help='Path to load and save encoder status (JSON)')

    parser.add_argument('--serial',
                        type=str,
                        default='/dev/ttyACM0',
                        help='Serial port to use for speed control (/dev/ttyUSB0)')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        log.setLevel(level=logging.DEBUG)
    else:
        logging.basicConfig()
        log.setLevel(level=logging.INFO)

    if args.state_store_path:
        atexit.register(save_state, path=args.state_store_path)

        def exit_handler(*a, **k):
            for device in devices.get():
                device.controller.closed_loop = False
            log.info('Halting motors')
            socketio.sleep(1)
            log.info('Halting done. Saving state')
            sys.exit(0)

        gevent.signal(signal.SIGTERM, exit_handler)
        gevent.signal(signal.SIGINT, exit_handler)
        gevent.signal(signal.SIGQUIT, exit_handler)
        initial_state.update(load_state(args.state_store_path))

    with open(args.config, 'r') as config_file:
        config = json.load(config_file)
        for idx, device_config in enumerate(config.get('devices', [])):
            device_config['initial_state'] = initial_state.get(device_config['id'], {})
            device = devices.create(**device_config)

        if not args.dry_run:
            serial_interface = SerialPortInterface(args.serial)
            for device in devices.get():
                device.serial_interface = serial_interface

    if not args.dry_run:
        for device in devices.get():
            log.info('Starting polling task for: %s', device)
            poller = build_polling_task(device)
            pollers.append(poller)

    # reloader launchs another thread for the main process and that means two instances of the controller and encoder poller but only one of them is managed by the UI. Fun times.
    socketio.run(app, host=args.host, port=args.port, use_reloader=False, debug=True, log_output=True)
