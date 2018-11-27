import attr

import control


# Default polling time in milliseconds
DEFAULT_INTERVAL = 50
# Default max speed in steps per second
DEFAULT_MAX_SPEED = 20000

__devices = []
__devices_by_id = {}


def get(name=None):
    if name is None:
        return __devices
    else:
        for device in __devices:
            if device.name == name:
                return device
    return None


@attr.s
class Device(object):
    name = attr.ib(default='')
    host = attr.ib(default=None)
    port = attr.ib(default=44818)
    steps = attr.ib(default=25600)
    axis = attr.ib(default='A')
    invert = attr.ib(default=False)
    gear_ratio_num = attr.ib(default=1)
    gear_ratio_den = attr.ib(default=1)
    offset = attr.ib(default=0)
    max_speed = attr.ib(default=DEFAULT_MAX_SPEED)
    interval = attr.ib(default=DEFAULT_INTERVAL)
    serial_port = attr.ib(default=None, init=False)
    controller = attr.ib(init=False, default=attr.Factory(control.ServoController, takes_self=True))


def create(**kwargs):
    device = Device(**kwargs)
    __devices.append(device)
    return device
