from flask_restplus import fields

from ethernet_servo.api import api


Device = api.model('Device', {
    'name': fields.String,
    'id':   fields.String,
    'host': fields.String,
    'port': fields.Integer,
    'steps': fields.Integer,
    'offset': fields.Integer(attribute='controller.state.offset'),
    'max_speed': fields.Integer,
    'interval': fields.Integer,
    'invert': fields.Boolean,
    'serial_port': fields.String,
    'supports_hour_angle': fields.Boolean,
    'can_track': fields.Boolean,
    'closed_loop': fields.Boolean(attribute='controller.state.closed_loop'),
    # XXX FIXME: 'controller': fields.
})


RawPosition = api.model('RawPosition', {
    'value': fields.Integer,
})


Tracking = api.model('Tracking', {
    'tracking': fields.Boolean,
})


AnglePosition = api.model('AnglePosition', {
    'degrees': fields.Integer,
    'minutes': fields.Integer,
    'seconds': fields.Float,
})


AstronomicalPosition = api.model('AstronomicalPosition', {
    'hours': fields.Integer,
    'minutes': fields.Integer,
    'seconds': fields.Float,
})


ControllerState = api.model('ControllerState', {
    'offset': fields.Integer(attribute='offset', default=0),
    'error': fields.Float(attribute='error', default=0),
    'position': fields.Float(attribute='position', default=0),
    'output': fields.Float(attribute='output', default=0),
    'max_slew_rate': fields.Float(attribute='pid.max_slew_rate', default=12000),
    'derivative_filtering': fields.Float(attribute='pid.derivative_filtering', default=0.75),
    'Kp': fields.Float(attribute='pid.Kp', default=1.8),
    'Ki': fields.Float(attribute='pid.Ki', default=1),
    'Kd': fields.Float(attribute='pid.Kd', default=1),
    # 'invert': fields.Boolean(attribute='device.invert'),
    'tracking': fields.Boolean(attribute='tracking', default=False),
    'free_running': fields.Boolean(attribute='free_running', default=False),
    'run_speed': fields.Nested(model=AnglePosition, attribute='run_speed'),
    'closed_loop': fields.Boolean(attribute='closed_loop', default=False),
    'target': fields.Float(attribute='target'),
})


DeviceStatus = api.model('DeviceStatus', {
    'name': fields.String,
    'tracking': fields.Boolean(attribute='controller.state.tracking'),
    'free_running': fields.Boolean(attribute='controller.state.free_running'),
    'run_speed': fields.Nested(model=AnglePosition, attribute='controller.state.run_speed'),
    'closed_loop': fields.Boolean(attribute='controller.state.closed_loop'),
    'target': fields.Float(attribute='controller.state.target'),
    'target_angle': fields.Nested(model=AnglePosition, attribute='controller.state.target_angle'),
    'target_astronomical': fields.Nested(model=AstronomicalPosition, attribute='controller.state.target_astronomical'),
    'position': fields.Float(attribute='controller.state.position'),
    'position_angle': fields.Nested(model=AnglePosition, attribute='controller.state.position_angle'),
    'position_astronomical': fields.Nested(model=AstronomicalPosition, attribute='controller.state.position_astronomical'),
    'error': fields.Float(attribute='controller.state.error'),
    'pid': fields.Nested(model=ControllerState, attribute='controller.state')
})
