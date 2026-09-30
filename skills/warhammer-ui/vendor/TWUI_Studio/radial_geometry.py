"""RadialList model calibrated from in-game experiments.

Arc is a slot budget (N slots, not N-1); this prevents duplicate endpoints on
full circles. Radius growth uses a non-overlap chord estimate, not CA's solver.
All stored/input angles are radians; screen y increases downwards.
"""
import math

ANGLE_KEYS = {'starting_angle', 'arc', 'spacing'}

def degrees_to_xml(value):
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 360:
        raise ValueError('Angle must be between 0 and 360 degrees')
    return repr(math.radians(number))

def xml_to_degrees(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('Angle must be finite')
    return math.degrees(number)

def radial_layout(values, count, diameter=48):
    def number(key, default):
        result = float(values.get(key, default))
        if not math.isfinite(result):
            raise ValueError(key)
        return result
    start = number('starting_angle', 0)
    arc = max(0, min(math.tau, number('arc', 0)))
    radius = max(0, number('radius', 95))
    spacing = max(0, number('spacing', 0))
    count = max(0, int(count))
    step = min(spacing, arc / count) if arc > 0 and count > 1 else spacing
    # Only expand after the arc budget compresses the requested spacing.
    # Deliberate spacing=0 remains coincident, and arc=0 remains unconstrained.
    if 0 < step < spacing and count > 1:
        radius = max(radius, max(0, diameter) / (2 * math.sin(min(math.pi, step) / 2)))
    direction = -1 if str(values.get('clockwise', 'false')).lower() == 'true' else 1
    angles = [start + direction * step * i for i in range(count)]
    def point(angle):
        return radius * math.cos(angle), -radius * math.sin(angle)
    points = [point(angle) for angle in angles]
    sweep = arc if arc else min(math.tau, step * max(0, count - 1))
    curve = [point(start + direction * sweep * i / 120) for i in range(121)]
    return points, curve, step, radius

def geometry(values, count, diameter=48):
    points, curve, _, _ = radial_layout(values, count, diameter)
    return points, curve
