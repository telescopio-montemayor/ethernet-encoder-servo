import control

from api import api, BaseResource
from . import models


ns = api.namespace('devices', description='Configured servo controllers')


@ns.route('/')
class DeviceList(BaseResource):
    @ns.doc('List of configured servo controllers')
    @ns.marshal_list_with(models.Device)
    def get(self, id=None):
        return control.devices.get()


@ns.route('/<string:name>')
@ns.param('name', 'The servo controller name as configured')
class DeviceStatus(BaseResource):
    @ns.doc('Status of a single servo controller')
    @ns.marshal_with(models.DeviceStatus)
    def get(self, name):
        return self.get_device(name)


@ns.route('/<string:name>/tracking')
@ns.param('name', 'The servo controller name as configured')
class DeviceTracking(BaseResource):
    @ns.doc('Set this servo to track or not the current AstronomicalPosition')
    @ns.marshal_with(models.DeviceStatus)
    @ns.expect(models.Tracking)
    def put(self, name):
        device = self.get_device(name)

        device.controller.tracking = api.payload['tracking']
        return device



