import tkinter as tk
from collections.abc import Callable
from typing import Optional

import theme


class VehiclePanel(tk.LabelFrame):
    def __init__(
        self,
        parent: tk.Misc,
        *,
        on_arm: Callable[[], None],
        on_takeoff: Callable[[], None],
    ) -> None:
        super().__init__(
            parent,
            text="Vehicle",
            bg=theme.SECTION_BG,
            fg=theme.MAIN_TEXT_COLOR,
            bd=0,
            padx=10,
            pady=10,
        )
        self.columnconfigure(0, weight=1)

        self._arm_btn = tk.Button(
            self,
            text="Arm",
            command=on_arm,
            state=tk.DISABLED,
            **theme.BUTTON_DEFAULTS,
            **{**theme.ARM_BUTTON_STYLE, "bg": theme.ARM_DISABLED_BG},
        )
        self._arm_btn.grid(row=0, column=0, padx=5, pady=5)

        self._takeoff_controls_frame = tk.Frame(self, bg=theme.SECTION_BG)
        self._takeoff_controls_frame.grid(row=1, column=0, pady=5)

        self._target_altitude_label = tk.Label(
            self._takeoff_controls_frame,
            text="Target altitude (m)",
            bg=theme.SECTION_BG,
            fg=theme.MAIN_TEXT_COLOR,
        )
        self._target_altitude_label.grid(row=0, column=0, padx=5)

        self._target_altitude_entry = tk.Entry(
            self._takeoff_controls_frame,
            bg=theme.INPUT_BG,
            fg=theme.MAIN_TEXT_COLOR,
            insertbackground=theme.MAIN_TEXT_COLOR,
            relief=tk.FLAT,
            bd=0,
            width=8,
            highlightthickness=1,
            highlightbackground=theme.SECONDARY_TEXT_COLOR,
            highlightcolor=theme.PRIMARY_BG,
        )
        self._target_altitude_entry.grid(row=0, column=1, padx=5)

        self._takeoff_btn = tk.Button(
            self._takeoff_controls_frame,
            text="Takeoff",
            command=on_takeoff,
            state=tk.DISABLED,
            **theme.BUTTON_DEFAULTS,
            **{**theme.ARM_BUTTON_STYLE, "bg": theme.ARM_DISABLED_BG},
        )
        self._takeoff_btn.grid(row=0, column=2, padx=5)

        self._current_altitude_label = tk.Label(
            self,
            text="Altitude: -",
            bg=theme.SECTION_BG,
            fg=theme.MAIN_TEXT_COLOR,
        )
        self._current_altitude_label.grid(row=2, column=0, pady=5)

    def get_target_altitude(self) -> str:
        return self._target_altitude_entry.get().strip()

    def set_altitude(self, altitude: Optional[float]) -> None:
        if altitude is None:
            self._current_altitude_label.config(text="Altitude: -")
        else:
            self._current_altitude_label.config(text=f"Altitude: {altitude:.1f} m")

    def set_arm_available(self, available: bool) -> None:
        desired_state = tk.NORMAL if available else tk.DISABLED
        if self._arm_btn.cget("state") != desired_state:
            self._arm_btn.config(
                state=desired_state,
                bg=theme.ARM_BG if available else theme.ARM_DISABLED_BG,
            )

    def set_takeoff_available(self, available: bool) -> None:
        desired_state = tk.NORMAL if available else tk.DISABLED
        if self._takeoff_btn.cget("state") != desired_state:
            self._takeoff_btn.config(
                state=desired_state,
                bg=theme.ARM_BG if available else theme.ARM_DISABLED_BG,
            )
