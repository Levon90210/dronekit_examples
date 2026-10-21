"""
12 - Flight modes tour: change the flight mode from code.

  [Connect] -> [Takeoff in GUIDED] -> [LOITER] -> [GUIDED] -> [LAND]
"""
import time

from dronekit import VehicleMode, connect


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


def set_mode(vehicle, name):
    vehicle.mode = VehicleMode(name)
    while vehicle.mode.name != name:     # wait until the autopilot confirms
        time.sleep(0.2)
    print("Mode is now", vehicle.mode.name)


# ---- BLOCK 1: Connect ----
vehicle = connect('127.0.0.1:14550', wait_ready=True)

# ---- BLOCK 2: Takeoff (GUIDED mode is required for simple_takeoff) ----
arm_and_takeoff(vehicle, 10)
time.sleep(10)
# ---- BLOCK 3: Visit other modes ----
set_mode(vehicle, "LOITER")     # hold position
time.sleep(5)
set_mode(vehicle, "GUIDED")     # accept commands from the script again
time.sleep(5)

# ---- BLOCK 4: Land ----
set_mode(vehicle, "LAND")
vehicle.close()
