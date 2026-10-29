from typing import Optional

from dronekit import Vehicle, VehicleMode, connect


class VehicleController:
    _REQUIRED_ATTRIBUTES = ["gps_0", "armed", "mode", "attitude"]

    def __init__(self) -> None:
        self._vehicle: Optional[Vehicle] = None

    @property
    def mode_name(self) -> Optional[str]:
        if self._vehicle is None or self._vehicle.mode is None:
            return None

        return self._vehicle.mode.name

    @property
    def is_armable(self) -> bool:
        if self._vehicle is None:
            return False

        return self._vehicle.is_armable

    @property
    def armed(self) -> bool:
        if self._vehicle is None:
            return False

        return self._vehicle.armed

    @property
    def can_arm(self) -> bool:
        if self._vehicle is None:
            return False

        return (
            self.mode_name in ["GUIDED", "STABILIZE", "LOITER"]
            and self.is_armable
            and not self.armed
        )

    def connect(self, connection_string: str) -> None:
        if self._vehicle is not None:
            raise RuntimeError("Vehicle is already connected")

        self._vehicle = connect(connection_string, wait_ready=self._REQUIRED_ATTRIBUTES)

    def disconnect(self) -> None:
        if self._vehicle is not None:
            self._vehicle.close()
            self._vehicle = None

    def set_mode(self, mode_name: str) -> None:
        if self._vehicle is None:
            raise RuntimeError("Vehicle is not connected")

        self._vehicle.mode = VehicleMode(name=mode_name)

    def arm(self) -> None:
        if self._vehicle is None:
            raise RuntimeError("Vehicle is not connected")

        if not self.can_arm:
            raise RuntimeError("Vehicle cannot be armed")

        self._vehicle.armed = True
