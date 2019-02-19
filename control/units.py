import math
import attr

from astropy.time import Time


SITE_LONGITUDE = -58.381592

# From libindi/libs/indicom.c


def range24(v):
    res = v
    while res < 0:
        res += 24.0
    while res > 24:
        res -= 24.0

    return res


def rangeDec(decdegrees):
    if ((decdegrees >= 270.0) and (decdegrees <= 360.0)):
        return (decdegrees - 360.0)
    if ((decdegrees >= 180.0) and (decdegrees < 270.0)):
        return (180.0 - decdegrees)
    if ((decdegrees >= 90.0) and (decdegrees < 180.0)):
        return (180.0 - decdegrees)

    return decdegrees


def LST(longitude=None):
    if longitude is None:
        longitude = SITE_LONGITUDE
    now = Time.now()
    lst = now.sidereal_time('apparent', longitude=longitude).to_value()
    return range24(lst)
# First call to sidereal_time() takes a while to initialize
LST()   # noqa


def deg_to_ra(deg, longitude=None):
    ra = deg / 15.0
    ra += LST(longitude=longitude)
    return range24(ra)


def ra_to_deg(ra, longitude=None):
    ra -= LST(longitude=longitude)
    deg = ra * 15.0
    deg = rangeDec(deg)
    return deg


def decimal_to_dms(angle):
    sign = 1.0
    if angle < 0:
        sign = -1.0
    angle = math.fabs(angle)

    degrees = math.floor(angle)

    minutes_float = (angle - degrees) * 60
    minutes = math.floor(minutes_float)

    seconds = (minutes_float - minutes) * 60

    degrees = degrees*sign
    minutes = minutes*sign
    seconds = seconds*sign
    return (degrees, minutes, seconds)


@attr.s
class AnglePosition:
    degrees = attr.ib(default=0)
    minutes = attr.ib(default=0)
    seconds = attr.ib(default=0)

    def to_decimal(self):
        return self.degrees + self.minutes / 60.0 + self.seconds / 3600.0

    def to_dict(self):
        return {
            'degrees': self.degrees,
            'minutes': self.minutes,
            'seconds': self.seconds
        }

    @classmethod
    def from_decimal(cls, angle):
        degrees, minutes, seconds = decimal_to_dms(angle)
        return cls(degrees, minutes, seconds)


@attr.s
class AstronomicalPosition:
    hours = attr.ib(default=0)
    minutes = attr.ib(default=0)
    seconds = attr.ib(default=0)
    longitude = attr.ib(default=None)

    @classmethod
    def from_degrees(cls, degrees, longitude=None):
        hours, minutes, seconds = decimal_to_dms(deg_to_ra(degrees, longitude))
        return cls(hours, minutes, seconds)

    def to_decimal(self):
        return self.hours + self.minutes / 60.0 + self.seconds / 3600.0

    def to_degrees(self):
        return ra_to_deg(self.to_decimal(), self.longitude)

    def to_dict(self):
        return {
            'hours':   self.hours,
            'minutes': self.minutes,
            'seconds': self.seconds,
            'longitude': self.longitude
        }
