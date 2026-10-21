"""
15 - Software geofence: stay inside a circle around home.

  [Takeoff] -> [Fly outward] -> loop: [distance from home > radius?] -yes-> [RTL]
"""
import math
import time

from dronekit import LocationGlobalRelative, VehicleMode, connect

FENCE_RADIUS = 40       # meters


def arm_and_takeoff(vehicle, target_altitude):
    while not vehicle.is_armable:
        time.sleep(1)
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True
    while not vehicle.armed:
        time.sleep(1)
    vehicle.simple_takeoff(target_altitude)
    while vehicle.location.global_relative_frame.alt < target_altitude * 0.95:
        time.sleep(1)


def distance_m(a, b):
    """Flat-earth distance in meters, good enough for short ranges."""
    dlat = (b.lat - a.lat) * 1.113195e5
    dlon = (b.lon - a.lon) * 1.113195e5 * math.cos(math.radians(a.lat))
    return math.sqrt(dlat ** 2 + dlon ** 2)


# ---- BLOCK 1: Connect, take off, remember home ----
vehicle = connect('127.0.0.1:14550', wait_ready=True)
arm_and_takeoff(vehicle, 15)
home = vehicle.location.global_relative_frame

# ---- BLOCK 2: Order the drone to go far away (further than the fence) ----
vehicle.simple_goto(LocationGlobalRelative(home.lat + 0.001, home.lon, 15))   # ~110 m

# ---- BLOCK 3: Check the fence ----
while True:
    d = distance_m(home, vehicle.location.global_relative_frame)
    print("Distance from home: %.1f m" % d)
    if d > FENCE_RADIUS:
        print("Fence breached! Returning to launch")
        vehicle.mode = VehicleMode("RTL")
        break
    time.sleep(1)

# ---- BLOCK 4: Close ----
vehicle.close()
