import ethernet_servo.control as control
from ethernet_servo.api import api, BaseResource

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


@ns.route('/<string:name>/run_speed')
@ns.param('name', 'The servo controller name as configured')
class DeviceFreeRun(BaseResource):
    @ns.doc('Set this servo to run at the specified degrees per second')
    @ns.marshal_with(models.DeviceStatus)
    @ns.expect(models.AnglePosition)
    def put(self, name):
        device = self.get_device(name)

        speed = control.units.AnglePosition()
        speed.degrees = api.payload['degrees']
        speed.minutes = api.payload['minutes']
        speed.seconds = api.payload['seconds']
        device.controller.run_speed = speed
        return device


@ns.route('/<string:name>/reset')
@ns.param('name', 'The servo controller name as configured')
class DeviceReset(BaseResource):
    @ns.doc('Set this servo target to current position')
    @ns.marshal_with(models.DeviceStatus)
    def get(self, name):
        device = self.get_device(name)

        device.controller.tracking = False
        device.controller.free_running = False
        device.controller.target_raw = device.controller.position
        return device


@ns.route('/<string:name>/halt')
@ns.param('name', 'The servo controller name as configured')
class DeviceHalt(BaseResource):
    @ns.doc('Set this servo to work in open loop, stops all motion')
    @ns.marshal_with(models.DeviceStatus)
    def put(self, name):
        device = self.get_device(name)

        device.controller.closed_loop = False
        device.controller.tracking = False
        return device


@ns.route('/<string:name>/resume')
@ns.param('name', 'The servo controller name as configured')
class DeviceResume(BaseResource):
    @ns.doc('Set this servo to work in closed loop')
    @ns.marshal_with(models.DeviceStatus)
    def put(self, name):
        device = self.get_device(name)

        device.controller.closed_loop = True
        return device
