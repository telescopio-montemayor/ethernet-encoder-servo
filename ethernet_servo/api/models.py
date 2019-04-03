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
    'offset': fields.Integer(attribute='controller.state.offset'),
    'output': fields.Float(attribute='controller.state.output'),
    'slew_rate_limit': fields.Float(attribute='controller.state.slew_rate_limit'),
    'Kp': fields.Float(attribute='controller.state.Kp'),
    'Ki': fields.Float(attribute='controller.state.Ki'),
    'Kd': fields.Float(attribute='controller.state.Kd'),
})
