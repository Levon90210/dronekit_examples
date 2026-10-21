"""
18 - Skip waypoints during an AUTO mission.

  [Takeoff] -> [Upload 4 waypoints] -> [AUTO] -> [after 10 s: jump to waypoint 3] -> [RTL]
"""
import time

from dronekit import Command, VehicleMode, connect
from pymavlink import mavutil


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
arm_and_takeoff(vehicle, 15)
p = vehicle.location.global_relative_frame

# ---- BLOCK 2: Upload four waypoints in a line ----
cmds = vehicle.commands
cmds.clear()
for i in range(1, 5):
    cmds.add(waypoint(p.lat + i * 0.0002, p.lon, 15))
cmds.upload()

# ---- BLOCK 3: Start the mission ----
vehicle.commands.next = 0
vehicle.mode = VehicleMode("AUTO")
time.sleep(10)

# ---- BLOCK 4: Change plans: jump to the last waypoint ----
print("Skipping to waypoint 3")
vehicle.commands.next = 3
while vehicle.commands.next < cmds.count:
    time.sleep(1)

# ---- BLOCK 5: Return home ----
vehicle.mode = VehicleMode("RTL")
vehicle.close()
