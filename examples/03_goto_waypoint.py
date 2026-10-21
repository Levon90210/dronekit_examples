import time

from dronekit import LocationGlobalRelative, Vehicle, VehicleMode, connect

from utils import horizontal_distance_m, wait_until


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
TARGET_ALTITUDE_M = 10.0
LATITUDE_OFFSET_DEGREES = 0.0005
LONGITUDE_OFFSET_DEGREES = 0.0005
WAYPOINT_TIMEOUT_SECONDS = 60
WAYPOINT_ACCEPTANCE_RADIUS_M = 2.0
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

    start_location = vehicle.location.global_relative_frame
    if start_location.lat is None or start_location.lon is None:
        raise RuntimeError("Current global position is unavailable")

    start_latitude = start_location.lat
    start_longitude = start_location.lon
    target_location = LocationGlobalRelative(
        lat=start_latitude + LATITUDE_OFFSET_DEGREES,
        lon=start_longitude + LONGITUDE_OFFSET_DEGREES,
        alt=TARGET_ALTITUDE_M,
    )

    print("Heading to waypoint")
    vehicle.simple_goto(location=target_location)

    waypoint_deadline = time.monotonic() + WAYPOINT_TIMEOUT_SECONDS

    while True:
        current_location = vehicle.location.global_relative_frame
        remaining_distance_m = horizontal_distance_m(
            first=current_location,
            second=target_location,
        )

        print(
            f"Position: "
            f"lat={current_location.lat}, "
            f"lon={current_location.lon}, "
            f"alt={current_location.alt}; "
            f"remaining={remaining_distance_m:.2f} m"
        )

        if remaining_distance_m <= WAYPOINT_ACCEPTANCE_RADIUS_M:
            print("Reached waypoint")
            break

        if time.monotonic() >= waypoint_deadline:
            raise TimeoutError("Vehicle did not reach the waypoint")

        time.sleep(1.0)

    vehicle.mode = VehicleMode(name="RTL")
    wait_until(
        condition=lambda: vehicle.mode.name == "RTL",
        timeout_seconds=10.0,
        timeout_message="Vehicle did not enter RTL mode",
    )

    print("Returning to launch and landing...")

    wait_until(
        condition=lambda: not vehicle.armed,
        timeout_seconds=120.0,
        timeout_message="Vehicle did not complete RTL and disarm",
    )

    print("RTL complete; vehicle disarmed")

except Exception:
    if vehicle.armed:
        print("Flight failed; requesting emergency landing")
        vehicle.mode = VehicleMode(name="LAND")

    raise

finally:
    vehicle.close()
