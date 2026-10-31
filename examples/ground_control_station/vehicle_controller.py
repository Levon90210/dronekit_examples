import math
import queue
from typing import Any, Optional

from dronekit import Vehicle, VehicleMode, connect


class VehicleController:
    _REQUIRED_ATTRIBUTES = ["gps_0", "armed", "mode", "attitude"]

    def __init__(self) -> None:
        self._vehicle: Optional[Vehicle] = None
        self._log_messages: queue.Queue[str] = queue.Queue()

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

    @property
    def relative_altitude(self) -> Optional[float]:
        if self._vehicle is None:
            return None
        
        return self._vehicle.location.global_relative_frame.alt

    def connect(self, connection_string: str) -> None:
        if self._vehicle is not None:
            raise RuntimeError("Vehicle is already connected")

        self._vehicle = connect(connection_string, wait_ready=self._REQUIRED_ATTRIBUTES)
        self._vehicle.add_message_listener("STATUSTEXT", self._on_status_text)

    def disconnect(self) -> None:
        if self._vehicle is not None:
            self._vehicle.remove_message_listener("STATUSTEXT", self._on_status_text)
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

    def takeoff(self, target_altitude: float) -> None:
        if self._vehicle is None:
            raise RuntimeError("Vehicle is not connected")

        if not math.isfinite(target_altitude) or target_altitude <= 0:
            raise RuntimeError(f"Invalid target altitude: {target_altitude}")
        
        if self.mode_name != "GUIDED":
            raise RuntimeError("Takeoff is only available in GUIDED mode")

        if not self.armed:
            raise RuntimeError("Vehicle is not armed")

        self._vehicle.simple_takeoff(target_altitude)

    def drain_log_messages(self) -> list[str]:
        messages: list[str] = []
        while True:
            try:
                messages.append(self._log_messages.get_nowait())
            except queue.Empty:
                return messages
     
    def _on_status_text(self, vehicle: Vehicle, name: str, message: Any) -> None:
        self._log_messages.put(message.text)
