"""
17 - Survey pattern: "lawnmower" grid uploaded as an AUTO mission.

  [Takeoff] -> [Build grid rows] -> [Upload mission] -> [AUTO mode] -> [Wait] -> [RTL]

  ->->->->->->
              |
  <-<-<-<-<-<-
  |
  ->->->->->->
"""
import math
import time

from dronekit import Command, VehicleMode, connect
from pymavlink import mavutil

ROWS = 4
ROW_LENGTH = 40         # meters
ROW_SPACING = 10        # meters
ALTITUDE = 15


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


def waypoint(lat, lon, alt):
    return Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                   mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, lat, lon, alt)


# ---- BLOCK 1: Connect and take off ----
vehicle = connect('127.0.0.1:14550', wait_ready=True)
arm_and_takeoff(vehicle, ALTITUDE)
start = vehicle.location.global_relative_frame

# ---- BLOCK 2: Build the grid (each row is two waypoints, direction alternates) ----
m_lat = 1.0 / 1.113195e5
m_lon = m_lat / math.cos(math.radians(start.lat))
cmds = vehicle.commands
cmds.clear()
for row in range(ROWS):
    north = row * ROW_SPACING
    ends = [0, ROW_LENGTH] if row % 2 == 0 else [ROW_LENGTH, 0]
    for east in ends:
        cmds.add(waypoint(start.lat + north * m_lat, start.lon + east * m_lon, ALTITUDE))

# ---- BLOCK 3: Upload and start the mission ----
cmds.upload()
vehicle.commands.next = 0
vehicle.mode = VehicleMode("AUTO")

# ---- BLOCK 4: Wait until the last waypoint is reached ----
last = cmds.count
while vehicle.commands.next < last:
    print("Heading to waypoint", vehicle.commands.next, "of", last)
    time.sleep(2)

# ---- BLOCK 5: Return home ----
vehicle.mode = VehicleMode("RTL")
vehicle.close()
