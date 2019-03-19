from ethernet_servo.control import units
from ethernet_servo.api import api, BaseResource

from . import models


ns = api.namespace('devices', description='Configured servo controllers')


@ns.route('/<string:name>/sync')
@ns.param('name', 'The servo controller name as configured')
class DeviceSyncRaw(BaseResource):
    @ns.doc('Syncs current position (raw encoder value)')
    @ns.marshal_with(models.DeviceStatus)
    @ns.expect(models.RawPosition)
    def put(self, name):
        device = self.get_device(name)
        device.controller.sync_raw(api.payload['value'])
        return device


@ns.route('/<string:name>/sync/astronomical')
@ns.param('name', 'The servo controller name as configured')
class DeviceSyncRaw(BaseResource):
    @ns.doc('Syncs current position (astronomical)')
    @ns.marshal_with(models.DeviceStatus)
    @ns.expect(models.AstronomicalPosition)
    def put(self, name):
        device = self.get_device(name)

        target = units.AstronomicalPosition()
        target.hours = api.payload['hours']
        target.minutes = api.payload['minutes']
        target.seconds = api.payload['seconds']
        device.controller.sync_astronomical(target)
        return device


# XXX FIXME: usar modelo de angle verdadero
@ns.route('/<string:name>/sync/angle')
@ns.param('name', 'The servo controller name as configured')
class DeviceSyncRaw(BaseResource):
    @ns.doc('Syncs current position (angle)')
    @ns.marshal_with(models.DeviceStatus)
    @ns.expect(models.AnglePosition)
    def put(self, name):
        device = self.get_device(name)

        target = units.AnglePosition()
        target.degrees = api.payload['degrees']
        target.minutes = api.payload['minutes']
        target.seconds = api.payload['seconds']
        device.controller.sync_angle(target.to_decimal())
        return device
