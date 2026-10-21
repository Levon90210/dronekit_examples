"""
11 - Telemetry dashboard: read live data from the drone.

  [Connect] -> [Read attributes in a loop] -> [Print one line per second] -> [Close]
"""
import time

from dronekit import connect

# ---- BLOCK 1: Connect ----
vehicle = connect('127.0.0.1:14550', wait_ready=True)

# ---- BLOCK 2: Read and print telemetry for 15 seconds ----
for _ in range(15):
    loc = vehicle.location.global_relative_frame
    print("Mode: %-8s | Alt: %5.1f m | Speed: %4.1f m/s | Heading: %3d | Sats: %d | Battery: %s"
          % (vehicle.mode.name, loc.alt, vehicle.groundspeed, vehicle.heading,
             vehicle.gps_0.satellites_visible, vehicle.battery.level))
    time.sleep(1)

# ---- BLOCK 3: Close ----
vehicle.close()
