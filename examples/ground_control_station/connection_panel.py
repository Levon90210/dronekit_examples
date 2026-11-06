from collections.abc import Callable
import tkinter as tk

import config
import theme


class ConnectionPanel(tk.LabelFrame):
    def __init__(
        self,
        parent: tk.Misc,
        *,
        on_connect: Callable[[], None],
        on_disconnect: Callable[[], bool],
    ) -> None:
        super().__init__(
            parent,
            text="Connection",
            bg=theme.SECTION_BG,
            fg=theme.MAIN_TEXT_COLOR,
            bd=0,
            padx=10,
            pady=10,
        )
        self.columnconfigure(1, weight=1)

        self._connection_label = tk.Label(
            self,
            text="Disconnected",
            bg=theme.SECTION_BG,
            fg=theme.SECONDARY_TEXT_COLOR,
        )
        self._connection_label.grid(row=0, columnspan=2, padx=5, pady=5)

        self._connection_string_label = tk.Label(
            self,
            text="Connection string",
            bg=theme.SECTION_BG,
            fg=theme.MAIN_TEXT_COLOR,
        )
        self._connection_string_label.grid(row=1, column=0, padx=5, pady=5)

        self._connection_entry = tk.Entry(
            self,
            bg=theme.INPUT_BG,
            fg=theme.MAIN_TEXT_COLOR,
            insertbackground=theme.MAIN_TEXT_COLOR,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=theme.SECONDARY_TEXT_COLOR,
            highlightcolor=theme.PRIMARY_BG,
        )
        self._connection_entry.insert(0, config.DEFAULT_CONNECTION_STRING)
        self._connection_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self._connection_buttons_frame = tk.Frame(self, bg=theme.SECTION_BG)
        self._connection_buttons_frame.grid(row=2, column=0, columnspan=2, pady=5)

        self._connect_btn = tk.Button(
            self._connection_buttons_frame,
            text="Connect",
            command=on_connect,
            **theme.BUTTON_DEFAULTS,
            **theme.PRIMARY_BUTTON_STYLE,
        )
        self._connect_btn.grid(row=0, column=0, padx=5)

        self._close_connection_btn = tk.Button(
            self._connection_buttons_frame,
            text="Close Connection",
            command=on_disconnect,
            state=tk.DISABLED,
            **theme.BUTTON_DEFAULTS,
            **theme.SECONDARY_BUTTON_STYLE,
        )
        self._close_connection_btn.grid(row=0, column=1, padx=5)

    def get_connection_string(self) -> str:
        return self._connection_entry.get().strip()

    def set_status(self, status: str) -> None:
        self._connection_label.config(text=status)

    def set_controls(self, *, connecting: bool, connected: bool) -> None:
        if connecting:
            self._connect_btn.config(state=tk.DISABLED)
            self._close_connection_btn.config(state=tk.DISABLED)
            self._connection_entry.config(state=tk.DISABLED)
        elif connected:
            self._connect_btn.config(state=tk.DISABLED)
            self._close_connection_btn.config(state=tk.NORMAL)
            self._connection_entry.config(state=tk.DISABLED)
        else:
            self._connect_btn.config(state=tk.NORMAL)
            self._close_connection_btn.config(state=tk.DISABLED)
            self._connection_entry.config(state=tk.NORMAL)
