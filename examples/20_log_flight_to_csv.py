"""
20 - Log flight data to a CSV file (open it in Excel or plot it later).

  [Takeoff] -> [Fly a short leg] -> loop: [read data] -> [write CSV row] -> [Land]
"""
import csv
import time

from dronekit import LocationGlobalRelative, VehicleMode, connect

OUTPUT_FILE = "flight_log.csv"


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
arm_and_takeoff(vehicle, 10)

# ---- BLOCK 2: Start moving ----
p = vehicle.location.global_relative_frame
vehicle.simple_goto(LocationGlobalRelative(p.lat + 0.0003, p.lon, 10))

# ---- BLOCK 3: Record 20 seconds of data ----
with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["time_s", "lat", "lon", "alt_m", "groundspeed_ms", "battery_voltage"])
    t0 = time.time()
    while time.time() - t0 < 20:
        loc = vehicle.location.global_relative_frame
        writer.writerow([round(time.time() - t0, 1), loc.lat, loc.lon, loc.alt,
                         vehicle.groundspeed, vehicle.battery.voltage])
        time.sleep(0.5)
print("Saved", OUTPUT_FILE)

# ---- BLOCK 4: Land ----
vehicle.mode = VehicleMode("LAND")
vehicle.close()
