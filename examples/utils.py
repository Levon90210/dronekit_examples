from collections.abc import Callable
import math
import time
from typing import Optional

from dronekit import LocationGlobalRelative


def wait_until(
    condition: Callable[[], bool],
    *,
    timeout_seconds: float,
    timeout_message: str,
    polling_interval_seconds: float = 1.0,
    progress_message: Optional[str] = None,
) -> None:
    deadline = time.monotonic() + timeout_seconds

    while not condition():
        if time.monotonic() >= deadline:
            raise TimeoutError(timeout_message)

        if progress_message is not None:
            print(progress_message)

        time.sleep(polling_interval_seconds)


EARTH_RADIUS_M = 6_371_000.0


def horizontal_distance_m(
    first: LocationGlobalRelative,
    second: LocationGlobalRelative,
) -> float:
    if (
        first.lat is None
        or first.lon is None
        or second.lat is None
        or second.lon is None
    ):
        raise RuntimeError("Cannot calculate distance without coordinates")

    first_latitude_rad = math.radians(first.lat)
    second_latitude_rad = math.radians(second.lat)

    latitude_difference_rad = math.radians(second.lat - first.lat)
    longitude_difference_rad = math.radians(second.lon - first.lon)

    haversine_value = (
        math.sin(latitude_difference_rad / 2.0) ** 2
        + math.cos(first_latitude_rad)
        * math.cos(second_latitude_rad)
        * math.sin(longitude_difference_rad / 2.0) ** 2
    )

    angular_distance = 2.0 * math.atan2(
        math.sqrt(haversine_value),
        math.sqrt(1.0 - haversine_value),
    )

    return EARTH_RADIUS_M * angular_distance
