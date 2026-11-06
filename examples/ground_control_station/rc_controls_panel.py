from collections.abc import Callable
import tkinter as tk

import config
from rc_channel_indicator import RCChannelIndicator
import theme


class RCControlsPanel(tk.LabelFrame):
    _CHANNEL_LAYOUT = {
        "roll": ("Roll", tk.HORIZONTAL, 0, 0, 2, "ew"),
        "pitch": ("Pitch", tk.VERTICAL, 1, 0, 1, "ns"),
        "throttle": ("Throttle", tk.VERTICAL, 1, 1, 1, "ns"),
        "yaw": ("Yaw", tk.HORIZONTAL, 2, 0, 2, "ew"),
    }

    def __init__(
        self, parent: tk.Misc, *, on_keyboard_toggle: Callable[[bool], None]
    ) -> None:
        super().__init__(
            parent,
            text="RC Controls",
            bg=theme.SECTION_BG,
            fg=theme.MAIN_TEXT_COLOR,
            bd=0,
            padx=10,
            pady=10,
        )
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self._on_keyboard_toggle = on_keyboard_toggle
        self._rc_values: dict[str, tk.IntVar] = {
            "roll": tk.IntVar(self, value=config.RC_CENTER),
            "pitch": tk.IntVar(self, value=config.RC_CENTER),
            "throttle": tk.IntVar(self, value=config.RC_MIN),
            "yaw": tk.IntVar(self, value=config.RC_CENTER),
        }
        self._indicators: dict[str, RCChannelIndicator] = {}

        for channel, settings in self._CHANNEL_LAYOUT.items():
            name, orient, row, column, columnspan, sticky = settings
            indicator = RCChannelIndicator(
                self,
                name=name,
                variable=self._rc_values[channel],
                orient=orient,
                minimum=config.RC_MIN,
                maximum=config.RC_MAX,
            )
            self._indicators[channel] = indicator

            indicator.grid(
                row=row,
                column=column,
                columnspan=columnspan,
                sticky=sticky,
                padx=10,
                pady=10,
            )

        self._keyboard_enabled = tk.BooleanVar(self, value=False)

        self._keyboard_control_btn = tk.Checkbutton(
            self,
            text="Enable keyboard control",
            variable=self._keyboard_enabled,
            command=lambda: self._on_keyboard_toggle(self._keyboard_enabled.get()),
            bg=theme.SECTION_BG,
            fg=theme.MAIN_TEXT_COLOR,
            selectcolor=theme.INPUT_BG,
            activebackground=theme.SECTION_BG,
            activeforeground=theme.MAIN_TEXT_COLOR,
        )
        self._keyboard_control_btn.grid(row=3, columnspan=2, padx=10, pady=10)

        self._keyboard_control_status_label = tk.Label(
            self,
            text="Keyboard control: OFF",
            bg=theme.SECTION_BG,
            fg=theme.MAIN_TEXT_COLOR,
        )
        self._keyboard_control_status_label.grid(row=4, columnspan=2, padx=10, pady=10)

        self.bind("<Button-1>", self._focus_controls)

        for indicator in self._indicators.values():
            indicator.bind("<Button-1>", self._focus_controls)

    def set_values(self, values: dict[str, int]) -> None:
        for channel, value in values.items():
            self._rc_values[channel].set(value)

    def set_keyboard_enabled(self, enabled: bool) -> None:
        self._keyboard_enabled.set(enabled)
        self._keyboard_control_status_label.config(
            text=f"Keyboard control: {'ON' if enabled else 'OFF'}"
        )
        if enabled:
            self.focus_set()

    def set_keyboard_available(self, available: bool) -> None:
        desired_state = tk.NORMAL if available else tk.DISABLED
        if self._keyboard_control_btn.cget("state") != desired_state:
            self._keyboard_control_btn.config(state=desired_state)

    def _focus_controls(self, event: tk.Event) -> None:
        self.focus_set()
