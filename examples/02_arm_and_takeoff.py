from collections.abc import Callable
import time
from typing import Optional

from dronekit import Vehicle, VehicleMode, connect

from utils import wait_until


def arm_and_takeoff(
    vehicle: Vehicle,
    target_altitude_m: float,
) -> None:
    print("Basic pre-arm checks")
    wait_until(
        condition=lambda: vehicle.is_armable,
        timeout_seconds=60.0,
        timeout_message="Vehicle did not become armable",
        progress_message=" Waiting for vehicle to initialize...",
    )

    print("Changing to GUIDED mode")
    vehicle.mode = VehicleMode(name="GUIDED")
    wait_until(
        condition=lambda: vehicle.mode.name == "GUIDED",
        timeout_seconds=10.0,
        timeout_message="Vehicle did not enter GUIDED mode",
    )

    print("Arming motors")
    vehicle.armed = True
    wait_until(
        condition=lambda: vehicle.armed,
        timeout_seconds=30.0,
        timeout_message="Vehicle did not arm",
        progress_message=" Waiting for arming...",
    )

    print("Taking off!")
    vehicle.simple_takeoff(
        alt=target_altitude_m,
    )

    minimum_altitude = target_altitude_m * MINIMUM_ALTITUDE_RATIO
    takeoff_deadline = time.monotonic() + 60.0
    while True:
        current_altitude = vehicle.location.global_relative_frame.alt
        if current_altitude is None:
            raise RuntimeError("Relative altitude is unavailable")
        print(f" Altitude: {current_altitude:.2f} m")

        if current_altitude >= minimum_altitude:
            print("Reached target altitude")
            break

        if time.monotonic() > takeoff_deadline:
            raise TimeoutError("Vehicle did not reach the takeoff altitude")

        time.sleep(1)


CONNECTION_STRING = "127.0.0.1:14550"
REQUIRED_ATTRIBUTES = ["gps_0", "armed", "mode", "attitude"]
TARGET_ALTITUDE_M = 20.0
MINIMUM_ALTITUDE_RATIO = 0.95

vehicle = connect(
    ip=CONNECTION_STRING,
    wait_ready=REQUIRED_ATTRIBUTES,
)

try:
    arm_and_takeoff(
        vehicle=vehicle,
        target_altitude_m=TARGET_ALTITUDE_M,
    )

    print("Landing")
    vehicle.mode = VehicleMode(name="LAND")
    wait_until(
        condition=lambda: vehicle.mode.name == "LAND",
        timeout_seconds=10.0,
        timeout_message="Vehicle did not enter LAND mode",
    )

    print("Waiting for landing and automatic disarming...")
    wait_until(
        condition=lambda: not vehicle.armed,
        timeout_seconds=120.0,
        timeout_message="Vehicle did not land and disarm",
    )
    print("Landed and disarmed")

except Exception:
    if vehicle.armed:
        print("Flight failed; requesting emergency landing")
        vehicle.mode = VehicleMode(name="LAND")

    raise

finally:
    vehicle.close()
