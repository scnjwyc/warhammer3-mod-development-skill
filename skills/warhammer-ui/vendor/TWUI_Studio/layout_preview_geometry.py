"""Schematic guides for the inspector, not modifications to XML geometry."""
import math

def radial_guide(values):
    def number(key,default):
        value=float(values.get(key,default))
        if not math.isfinite(value):raise ValueError(key)
        return value
    start=number('starting_angle',0)
    arc=max(0,min(math.tau,number('arc',0)))
    spacing=max(0,number('spacing',0))
    radius=max(0,number('radius',95))
    direction=-1 if str(values.get('clockwise','false')).lower()=='true' else 1
    def points(r,step,count):
        return [(r*math.cos(start+direction*step*i),-r*math.sin(start+direction*step*i)) for i in range(count)]
    requested=points(radius,spacing,5)
    # A large step can wrap back onto earlier buttons, even with arc disabled.
    overlaps=spacing>math.tau/5 and any(math.dist(requested[i],requested[j])<48 for i in range(5) for j in range(i))
    expanded=spacing>0 and ((arc>0 and 4*spacing>arc+1e-9) or overlaps or 4*spacing>=math.tau)
    step=spacing
    effective=radius
    if expanded:
        step=min(spacing,(arc or math.tau)/6)
        effective=max(radius+16,radius*1.18,48/(2*math.sin(step/2)))
    sweep=arc or min(math.tau,spacing*4)
    def curve(r):
        return [(r*math.cos(start+direction*sweep*i/120),-r*math.sin(start+direction*sweep*i/120)) for i in range(121)]
    return {'points':points(effective,step,6 if expanded else 5)[:5], 'base_curve':curve(radius),
            'expanded_curve':curve(effective) if expanded else None, 'radius':effective,
            'step':step,'slots':6 if expanded else 5}

def list_guide(kind,children):
    # Fixed schematic spacing: show order/direction, not a game layout solver.
    return [(child, index*110 if kind=='HorizontalList' else 0,
             index*60 if kind=='List' else 0) for index,child in enumerate(children[:5])]
