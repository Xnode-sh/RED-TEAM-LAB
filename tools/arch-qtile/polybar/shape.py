#!/usr/bin/env python3
"""Clip Polybar windows to rounded X11 regions, including without a compositor."""
import math
import time
import xcffib
import xcffib.shape
import xcffib.xproto
from panel import ipc

def rounded_rectangles(width, height, radius):
    radius = min(radius, height / 2, width / 2)
    rectangles = []
    for y in range(height):
        edge = min(y, height - 1 - y)
        inset = math.ceil(radius - math.sqrt(max(0, radius**2 - (radius-edge-.5)**2))) if edge < radius else 0
        rectangles.append(xcffib.xproto.RECTANGLE.synthetic(inset, y, width - 2*inset, 1))
    return rectangles

def main():
    # Let panels terminated by launch.sh leave the X11 client list first.
    time.sleep(.2)
    connection = xcffib.connect()
    extension = connection(xcffib.shape.key)
    names = ('control', 'clock', 'status', 'telemetry')
    completed = set()
    try:
        for _ in range(30):
            for window in ipc('windows'):
                name = window.get('name', '')
                if not any(name.startswith('polybar-'+bar+'_') for bar in names):
                    continue
                wid = window['id']
                if wid in completed:
                    continue
                geometry = connection.core.GetGeometry(wid).reply()
                rectangles = rounded_rectangles(geometry.width, geometry.height, 14)
                extension.Rectangles(xcffib.shape.SO.Set, xcffib.shape.SK.Bounding,
                                     xcffib.xproto.ClipOrdering.Unsorted, wid, 0, 0,
                                     len(rectangles), rectangles, is_checked=True).check()
                connection.flush()
                assert extension.QueryExtents(wid).reply().bounding_shaped
                completed.add(wid)
            if len(completed) >= len(names):
                print('Rounded X11 shapes applied to all four panels')
                return
            time.sleep(.1)
        raise RuntimeError(f'Only {len(completed)} panel windows found')
    finally:
        connection.disconnect()

if __name__ == '__main__':
    main()
