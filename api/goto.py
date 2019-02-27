from control import units

from api import api, BaseResource
from . import models


ns = api.namespace('devices', description='Configured servo controllers')


@ns.route('/<string:name>/goto')
@ns.param('name', 'The servo controller name as configured')
class DeviceGotoRaw(BaseResource):
    @ns.doc('Sets target position (raw encoder value)')
    @ns.marshal_with(models.DeviceStatus)
    @ns.expect(models.RawPosition)
    def put(self, name):
        device = self.get_device(name)
        device.controller.target_raw = api.payload['value']
        return device


@ns.route('/<string:name>/goto/astronomical')
@ns.param('name', 'The servo controller name as configured')
class DeviceGotoAstronomical(BaseResource):
    @ns.doc('Sets target position (astronomical)')
    @ns.marshal_with(models.DeviceStatus)
    @ns.expect(models.AstronomicalPosition)
    def put(self, name):
        device = self.get_device(name)

        target = units.AstronomicalPosition()
        target.hours = api.payload['hours']
        target.minutes = api.payload['minutes']
        target.seconds = api.payload['seconds']
        device.controller.target_astronomical = target
        return device


@ns.route('/<string:name>/goto/angle')
@ns.param('name', 'The servo controller name as configured')
class DeviceGotoAngle(BaseResource):
    @ns.doc('Sets target position (angle)')
    @ns.marshal_with(models.DeviceStatus)
    @ns.expect(models.AnglePosition)
    def put(self, name):
        device = self.get_device(name)

        target = units.AnglePosition()
        target.degrees = api.payload['degrees']
        target.minutes = api.payload['minutes']
        target.seconds = api.payload['seconds']
        device.controller.target_angle = target.to_decimal()
        return device


@ns.route('/<string:name>/goto/relative/angle')
@ns.param('name', 'The servo controller name as configured')
class DeviceGotoRelativeAngle(BaseResource):
    @ns.doc('Sets target position (angle) relative to current position')
    @ns.marshal_with(models.DeviceStatus)
    @ns.expect(models.AnglePosition)
    def put(self, name):
        device = self.get_device(name)

        current_target = device.controller.target_angle
        current_target.degrees += api.payload['degrees']
        current_target.minutes += api.payload['minutes']
        current_target.seconds += api.payload['seconds']

        device.controller.target_angle = current_target

        return device


@ns.route('/<string:name>/goto/relative/astronomical')
@ns.param('name', 'The servo controller name as configured')
class DeviceGotoRelativeAngle(BaseResource):
    @ns.doc('Sets target position (astronomical) relative to current position')
    @ns.marshal_with(models.DeviceStatus)
    @ns.expect(models.AstronomicalPosition)
    def put(self, name):
        device = self.get_device(name)

        current_target = device.controller.target_astronomical

        current_target.hours += api.payload['hours']
        current_target.minutes += api.payload['minutes']
        current_target.seconds += api.payload['seconds']

        device.controller.target_astronomical = current_target

        return device
