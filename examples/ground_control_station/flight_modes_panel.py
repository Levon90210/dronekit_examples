from collections.abc import Callable
import tkinter as tk
from typing import Optional

import config
import theme


class FlightModesPanel(tk.LabelFrame):
    def __init__(
        self, parent: tk.Misc, *, on_mode_selected: Callable[[str], None]
    ) -> None:
        super().__init__(
            parent,
            text="Flight modes",
            bg=theme.SECTION_BG,
            fg=theme.MAIN_TEXT_COLOR,
            bd=0,
            padx=10,
            pady=10,
        )

        self._current_mode_label = tk.Label(
            self, text="Current mode: -", bg=theme.SECTION_BG, fg=theme.MAIN_TEXT_COLOR
        )
        self._current_mode_label.grid(
            row=0, columnspan=len(config.MODE_LIST), padx=5, pady=5
        )

        self._mode_btn_map = {
            mode: tk.Button(
                self,
                text=mode,
                command=lambda mode=mode: on_mode_selected(mode),
                state=tk.DISABLED,
                **theme.BUTTON_DEFAULTS,
                **theme.SECONDARY_BUTTON_STYLE,
            )
            for mode in config.MODE_LIST
        }
        for i, btn in enumerate(self._mode_btn_map.values()):
            self.columnconfigure(i, weight=1, uniform="modes")
            btn.grid(row=1, column=i, padx=5, pady=5, sticky="ew")

    def set_mode(self, mode_name: Optional[str]) -> None:
        if mode_name is None:
            self._current_mode_label.config(text="Current mode: -")
        else:
            self._current_mode_label.config(text=f"Current mode: {mode_name}")

    def set_available(self, available: bool) -> None:
        desired_state = tk.NORMAL if available else tk.DISABLED
        for btn in self._mode_btn_map.values():
            if btn.cget("state") != desired_state:
                btn.config(state=desired_state)
