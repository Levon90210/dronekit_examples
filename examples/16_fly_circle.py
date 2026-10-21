"""
16 - Fly a circle: waypoints from trigonometry.

  [Takeoff] -> [Compute points: x = r*cos(a), y = r*sin(a)] -> [goto each point] -> [RTL]
"""
import math
import time

from dronekit import LocationGlobalRelative, VehicleMode, connect

RADIUS = 20             # meters
POINTS = 12             # 360 / 12 = 30 degrees per step


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


def offset_location(origin, north, east, alt):
    """Return a location `north`/`east` meters away from origin."""
    lat = origin.lat + north / 1.113195e5
    lon = origin.lon + east / (1.113195e5 * math.cos(math.radians(origin.lat)))
    return LocationGlobalRelative(lat, lon, alt)


# ---- BLOCK 1: Connect and take off ----
vehicle = connect('127.0.0.1:14550', wait_ready=True)
arm_and_takeoff(vehicle, 15)
center = vehicle.location.global_relative_frame

# ---- BLOCK 2: Compute the circle waypoints ----
waypoints = []
for i in range(POINTS + 1):
    angle = math.radians(i * 360 / POINTS)
    waypoints.append(offset_location(center, RADIUS * math.cos(angle), RADIUS * math.sin(angle), 15))

# ---- BLOCK 3: Visit them one by one ----
for i, wp in enumerate(waypoints):
    print("Waypoint", i)
    vehicle.simple_goto(wp, groundspeed=5)
    time.sleep(6)

# ---- BLOCK 4: Go home ----
vehicle.mode = VehicleMode("RTL")
vehicle.close()
