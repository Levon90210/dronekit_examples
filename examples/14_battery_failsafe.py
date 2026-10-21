"""
14 - Battery failsafe: our own safety rule written in Python.

  [Takeoff] -> [Fly away] -> loop: [battery < limit?] -yes-> [RTL]
                                                     -no--> [keep flying]
"""
import time

from dronekit import LocationGlobalRelative, VehicleMode, connect

BATTERY_LIMIT = 10.5      # voltage. Deliberately high so it triggers in the simulator.


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

# ---- BLOCK 2: Start a flight ----
home = vehicle.location.global_relative_frame
vehicle.simple_goto(LocationGlobalRelative(home.lat + 0.0003, home.lon, 15))

# ---- BLOCK 3: Monitor the battery ----
while True:
    voltage = vehicle.battery.voltage
    print("Battery:", voltage, "V")
    if voltage is not None and voltage < BATTERY_LIMIT:
        print("Battery low! Returning to launch")
        vehicle.mode = VehicleMode("RTL")
        break
    time.sleep(2)

# ---- BLOCK 4: Close ----
vehicle.close()
