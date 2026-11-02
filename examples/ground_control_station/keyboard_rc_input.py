import config


class KeyboardRCInput:
    _AXIS_KEYS = {
        "roll": ("left", "right"),
        "pitch": ("up", "down"),
        "yaw": ("a", "d"),
    }

    def __init__(self) -> None:
        self._values: dict[str, int] = {
            "roll": config.RC_CENTER,
            "pitch": config.RC_CENTER,
            "throttle": config.RC_MIN,
            "yaw": config.RC_CENTER,
        }

    def reset(self, *, throttle: int) -> None:
        self._values["roll"] = config.RC_CENTER
        self._values["pitch"] = config.RC_CENTER
        self._values["yaw"] = config.RC_CENTER
        self._values["throttle"] = throttle

    def update(self, *, pressed_keys: set[str]) -> None:
        for channel, (decrease_key, increase_key) in self._AXIS_KEYS.items():
            direction = int(increase_key in pressed_keys) - int(
                decrease_key in pressed_keys
            )
            self._values[channel] = (
                self._clamp(self._values[channel] + config.RC_AXIS_STEP * direction)
                if direction != 0
                else config.RC_CENTER
            )

        self._values["throttle"] = self._clamp(
            self._values["throttle"]
            + config.RC_THROTTLE_STEP
            * (int("w" in pressed_keys) - int("s" in pressed_keys))
        )

    @property
    def values(self) -> dict[str, int]:
        return self._values.copy()

    @staticmethod
    def _clamp(value: int) -> int:
        return max(config.RC_MIN, min(config.RC_MAX, value))
