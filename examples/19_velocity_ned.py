"""
19 - Velocity control in the NED frame (North, East, Down).

  [Takeoff] -> [send velocity N] -> [send velocity E] -> [send velocity S] -> [send velocity W] -> [RTL]

  NED: +x = North, +y = East, +z = DOWN (so negative z means climb).
"""
import time

from dronekit import VehicleMode, connect
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


def send_velocity(vehicle, vx, vy, vz, duration):
    """Send a velocity command (m/s) once per second for `duration` seconds."""
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0, 0, 0,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        # 0b011111000111 Not changin heading direction.
        0b0000111111000111,             # use only the velocity fields
        0, 0, 0,                        # position (ignored)
        vx, vy, vz,                     # velocity
        0, 0, 0,                        # acceleration (ignored)
        0, 0)                           # yaw, yaw rate (ignored)
    for _ in range(duration):
        vehicle.send_mavlink(msg)
        time.sleep(1)


# ---- BLOCK 1: Connect and take off ----
vehicle = connect('127.0.0.1:14550', wait_ready=True)
arm_and_takeoff(vehicle, 10)

# ---- BLOCK 2: Fly a square, 5 s per side at 3 m/s (~15 m) ----
print("North");  send_velocity(vehicle, 3, 0, 0, 5)
print("East");   send_velocity(vehicle, 0, 3, 0, 5)
print("South");  send_velocity(vehicle, -3, 0, 0, 5)
print("West");   send_velocity(vehicle, 0, -3, 0, 5)
print("Up");     send_velocity(vehicle, 0, 0, -3, 5)
print("Down");   send_velocity(vehicle, 0, 0, 3, 5)

# ---- BLOCK 3: Stop and go home ----
send_velocity(vehicle, 0, 0, 0, 2)
vehicle.mode = VehicleMode("RTL")
vehicle.close()
