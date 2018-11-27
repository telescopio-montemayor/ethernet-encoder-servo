import logging

from flask import current_app as app
from flask import Blueprint

from flask_restplus import Api, Resource
from flask_cors import CORS


import control


log = logging.getLogger(__name__)

blueprint = Blueprint('api', __name__, url_prefix='/api')
api = Api(blueprint, version='1.0', title='Ethernet Encoder Servo', description='')


def register(application):
    """Register this API endpoints within an application"""
    application.register_blueprint(blueprint)
    cors = CORS(application, resources={
        r"/api/*": {
            "origins": "*",
            "supports_credentials": True,
        }
    })


@api.errorhandler
def default_error_handler(e):
    message = 'An unhandled exception occurred.'
    log.exception(message)

    if not app.debug:
        return {'message': message}, 500


class BaseResource(Resource):
    def get_device(self, name):
        device = control.devices.get(name)
        if device is not None:
            return device
        else:
            api.abort(404, "Device '{}' does not exist".format(name))


from . import devices, goto, sync
__all__ = ['models', 'devices', 'goto', 'sync']
