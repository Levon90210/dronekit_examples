"""
13 - Return to launch (RTL): fly away, then come back automatically.

  [Takeoff] -> [Fly 30 m north] -> [Switch to RTL] -> [Wait for landing]
"""
import time

from dronekit import LocationGlobalRelative, VehicleMode, connect


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


# ---- BLOCK 1: Connect and take off ----
vehicle = connect('127.0.0.1:14550', wait_ready=True)
arm_and_takeoff(vehicle, 15)

# ---- BLOCK 2: Fly away from home (~0.00027 deg latitude = 30 m) ----
home = vehicle.location.global_relative_frame
target = LocationGlobalRelative(home.lat + 0.00027, home.lon + 0.00027, 5)
vehicle.simple_goto(target)
time.sleep(15)

# ---- BLOCK 3: Return to launch ----
print("Returning to launch")
vehicle.mode = VehicleMode("RTL")

# ---- BLOCK 4: Wait until the drone has landed and disarmed ----
while vehicle.armed:
    print(" Alt: %.1f" % vehicle.location.global_relative_frame.alt)
    time.sleep(2)
print("Landed at home")
vehicle.close()
