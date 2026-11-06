import tkinter as tk
from tkinter.scrolledtext import ScrolledText

import theme


class LogsPanel(tk.LabelFrame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(
            parent,
            text="Logs",
            bg=theme.SECTION_BG,
            fg=theme.MAIN_TEXT_COLOR,
            bd=0,
            padx=10,
            pady=10,
        )
        self._logs_area = ScrolledText(self, state=tk.DISABLED, **theme.LOG_AREA_STYLE)
        self._logs_area.pack(fill="both", expand=True)

    def append(self, message: str) -> None:
        self._logs_area.config(state=tk.NORMAL)
        self._logs_area.insert("end", message + "\n")
        self._logs_area.see("end")
        self._logs_area.config(state=tk.DISABLED)
