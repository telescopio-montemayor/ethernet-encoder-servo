import datetime
from collections import deque

from ethernet_servo.control.units import AnglePosition, AstronomicalPosition

STEPS_PER_REVOLUTION = 25600
COUNTS_PER_REVOLUTION = 262144
COUNTS_PER_STEP = 1.0 * COUNTS_PER_REVOLUTION / STEPS_PER_REVOLUTION


def cps_to_hz(cps, counts_per_step=COUNTS_PER_STEP):
    """ Converts encoder counts per second to step rate in hertz"""
    return cps / counts_per_step


def hz_to_cps(hz, counts_per_step=COUNTS_PER_STEP):
    return counts_per_step * hz


def update_stepper_freq(freq, device):
    serial_port = device.serial_port
    if not serial_port:
        return

    freq = saturate(freq, device.max_speed)

    payload = '\n{0}{1:-7.0f}\n'.format(device.axis, freq).encode('ascii')
    serial_port.write(payload)
    serial_port.flush()


def slew_rate_limit(next_value, current_value, slew_rate):
    delta = next_value - current_value

    if slew_rate is None:
        return next_value

    if delta > slew_rate:
        return current_value + slew_rate

    if delta < -slew_rate:
        return current_value - slew_rate

    return next_value


class SlewRateLimiter:
    def __init__(self, slew_rate, initial_value=0):
        self.slew_rate = slew_rate
        self.current_value = initial_value

    def process(self, next_value):
        output = slew_rate_limit(next_value, self.current_value, self.slew_rate)
        self.current_value = output
        return output


def saturate(value, max_limit, min_limit=None):
    if max_limit is None:
        return value

    if min_limit is None:
        min_limit = -max_limit

    if value > max_limit:
        return max_limit

    if value < min_limit:
        return min_limit

    return value


class SaturationLimiter:
    def __init__(self, max_limit, min_limit=None):
        self.max_limit = max_limit
        self.min_limit = min_limit
        self.current_value = 0

    def process(self, next_value):
        output = saturate(next_value, self.max_limit, self.min_limit)
        self.current_value = output
        return output


class MovingAverage:
    def __init__(self, length=30):
        self.length = length
        self.q = deque(maxlen=length)
        self.average = 0

    def process(self, value):
        self.q.append(value)
        non_zero = [x for x in self.q if x != 0]
        if non_zero:
            self.average = sum(non_zero) / len(non_zero)
        return self.average


def deadband(value, max_limit, min_limit=None):
    if max_limit is None:
        return value

    if min_limit is None:
        min_limit = -max_limit

    if value >= max_limit:
        return value

    if value <= min_limit:
        return value

    return 0


class DeadBand:
    def __init__(self, max_limit, min_limit=None):
        self.max_limit = max_limit
        self.min_limit = min_limit
        self.current_value = 0

    def process(self, next_value):
        output = deadband(next_value, self.max_limit, self.min_limit)
        self.current_value = output
        return output


class IIRLp:
    def __init__(self, alpha=0.9, sample_time=1.0/10):
        self.last_output = 0
        self.alpha = alpha
        self.sample_time = sample_time

    def process(self, value):
        output = self.alpha*value + (1-self.alpha)*self.last_output
        self.last_output = output
        return output


class PidController:
    def __init__(self, P=1.8, I=1.0, D=1.0, saturation_limit=None, sample_time=1.0/10, slew_rate=None, deadband=None):

        self.Kp = P
        self.Ki = I
        self.Kd = D
        self.windup_guard = 4000
        self.sample_time = sample_time
        self.slew_rate = slew_rate
        self.saturation_limit = saturation_limit

        self.derivative_filter = IIRLp()
        self.derivative_filter.alpha = .75

        self.deadband = DeadBand(deadband)
        self.slew_rate_limiter = SlewRateLimiter(slew_rate)

        self.clear()

    def clear(self):
        self.SetPoint = 0.0

        self.PTerm = 0.0
        self.ITerm = 0.0
        self.DTerm = 0.0

        self.is_saturated = False
        self.last_output = 0
        self.last_error = 0
        self.last_input = 0

    def update(self, feedback_value):

        #error = self.slew_rate_limiter.process(self.SetPoint) - feedback_value
        error = self.deadband.process(self.SetPoint - feedback_value)

        self.PTerm = self.Kp * error

        if not self.is_saturated:
            self.ITerm += error * self.sample_time
        self.ITerm = saturate(self.ITerm, self.windup_guard)

        self.DTerm = self.derivative_filter.process((error - self.last_error) / self.sample_time)

        self.last_error = error
        self.last_input = feedback_value

        output = self.PTerm + (self.Ki * self.ITerm) + (self.Kd * self.DTerm)

        output = self.slew_rate_limiter.process(output)
        limited_output = saturate(output, self.saturation_limit)
        if limited_output != output:
            self.is_saturated = True
        else:
            self.is_saturated = False

        output = limited_output
        self.last_output = output

        return output


class ServoController:
    def __init__(self, device):
        self.device = device
        self.ANGLE_TO_RAW = (COUNTS_PER_REVOLUTION / 360.0) / (device.gear_ratio_num / device.gear_ratio_den)
        self.RAW_TO_ANGLE = 1.0 / self.ANGLE_TO_RAW

        # XXX FIXME: steps per second squared from degrees/s**2
        SLEW_RATE_LIMIT = (10) * (1/360.) * device.steps * (device.gear_ratio_den / device.gear_ratio_num) * (device.interval / 1000.0)
        DEADBAND_LIMIT = COUNTS_PER_REVOLUTION / (2.0 * device.steps)

        self._state = {
            'closed_loop': True,
            'old_value': None,
            'old_timestamp': None,
            'position': 0,  # this takes into account wraparounds
            'speed_cps': 0,
            'speed_hz': 0,
            'dt': device.interval / 1000,
            'offset': 0,
        }
        self.position_filter = MovingAverage(length=3)
        self.pid_controller = PidController(slew_rate=SLEW_RATE_LIMIT, saturation_limit=hz_to_cps(device.max_speed, device.steps), deadband=DEADBAND_LIMIT)
        self.pid_controller.sample_time = device.interval / 1000
        self.pid_controller.SetPoint = 0
        self.tracking = False
        self._astronomical_target = None

    @property
    def state(self):
        state = dict(self._state)

        state.update({
            'tracking': self.tracking,
            'target': self.target_raw,
            'target_angle': self.target_angle,
            'target_astronomical': self.target_astronomical,
            'position_angle': self.position_angle,
            'position_astronomical': self.position_astronomical,
            'Kp': self.pid_controller.Kp,
            'Ki': self.pid_controller.Ki,
            'Kd': self.pid_controller.Kd,
            'alpha': self.pid_controller.derivative_filter.alpha,
            'slew_rate_limit': self.pid_controller.slew_rate,
            'error': self.pid_controller.last_error,
            'output': self.pid_controller.last_output,
        })
        state.pop('old_timestamp', None)
        return state

    @property
    def closed_loop(self):
        return self._state['closed_loop']

    @closed_loop.setter
    def closed_loop(self, value):
        self._state['closed_loop'] = bool(value)

    @property
    def target_raw(self):
        return self.pid_controller.SetPoint

    @target_raw.setter
    def target_raw(self, raw_target):
        self.pid_controller.SetPoint = raw_target + self._state['offset']
        self._astronomical_target = AstronomicalPosition.from_degrees(self.target_angle.to_decimal())

    @property
    def target_angle(self):
        target = self.target_raw * self.RAW_TO_ANGLE
        return AnglePosition.from_decimal(target)

    @target_angle.setter
    def target_angle(self, angle):
        try:
            self.target_raw = angle * self.ANGLE_TO_RAW
        except TypeError:
            self.target_raw = angle.to_decimal() * self.ANGLE_TO_RAW

    @property
    def target_astronomical(self):
        if self._astronomical_target is not None:
            return self._astronomical_target
        return AstronomicalPosition.from_degrees(self.target_angle.to_decimal())

    @target_astronomical.setter
    def target_astronomical(self, target):
        self.target_angle = target.to_degrees()
        self._astronomical_target = target
        self.tracking = True

    @property
    def position(self):
        return self._state['position'] - self._state['offset']

    @property
    def position_angle(self):
        angle = self.position * self.RAW_TO_ANGLE
        return AnglePosition.from_decimal(angle)

    @property
    def position_astronomical(self):
        return AstronomicalPosition.from_degrees(self.position_angle.to_decimal())

    def sync_raw(self, real_raw_position):
        self._state['offset'] = self._state['position'] - real_raw_position

    def sync_angle(self, real_angle_position):
        return self.sync_raw(real_angle_position * self.ANGLE_TO_RAW)

    def sync_astronomical(self, real_astronomical_position):
        self.tracking = True
        return self.sync_raw(real_astronomical_position.to_degrees() * self.ANGLE_TO_RAW)

    def update(self, feedback_value):
        state = self._state
        device = self.device

        now = datetime.datetime.now()
        now_formatted = now.isoformat()

        if device.invert:
            feedback_value = COUNTS_PER_REVOLUTION - feedback_value

        if state['old_value'] is None:
            state['position'] = feedback_value
            state['old_value'] = feedback_value

        new_position = state['position']
        dv = feedback_value - state['old_value']
        dv_abs = abs(dv)
        dv_wrapped = min(dv_abs, min((dv % COUNTS_PER_REVOLUTION), (COUNTS_PER_REVOLUTION - dv_abs)))

        if dv_wrapped == dv_abs:
            new_position += 1*dv
        else:
            if dv >= 0:
                dv_wrapped = -1 * dv_wrapped

            new_position += 1*dv_wrapped

        state['position'] = new_position
        state['old_value'] = feedback_value

        new_position = self.position_filter.process(new_position)
        position = new_position

        if state['old_timestamp'] is not None:
            state['dt'] = (now - state['old_timestamp']).total_seconds()

        state['old_timestamp'] = now
        # FIXME XXX device['timestamp'] = now_formatted

        if self.tracking:
            self.pid_controller.SetPoint = self.target_astronomical.to_degrees() * self.ANGLE_TO_RAW

        if state['closed_loop']:
            new_cps = self.pid_controller.update(position)
        else:
            self.target_raw = position

        if device.invert:
            new_cps = -1.0 * new_cps

        counts_per_step = 1.0 * COUNTS_PER_REVOLUTION / device.steps
        new_speed = cps_to_hz(new_cps, counts_per_step)
        state['speed_cps'] = new_cps
        state['speed_hz'] = new_speed

        if state['closed_loop']:
            update_stepper_freq(new_speed, device)

        return new_speed
