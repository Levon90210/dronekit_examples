import tkinter as tk

import theme


class RCChannelIndicator(tk.Canvas):
    def __init__(
        self,
        parent: tk.Misc,
        *,
        name: str,
        variable: tk.IntVar,
        orient: str,
        minimum: int,
        maximum: int,
    ) -> None:
        height = 30 if orient == tk.HORIZONTAL else 200
        width = 200 if orient == tk.HORIZONTAL else 40
        super().__init__(
            parent,
            height=height,
            width=width,
            bg=theme.INDICATOR_BG,
            highlightthickness=0,
            bd=0,
        )

        self._name = name
        self._variable = variable
        self._orient = orient
        self._minimum = minimum
        self._maximum = maximum

        self._fill_id = self.create_rectangle(
            0, 0, 100, 30, fill=theme.INDICATOR_FILL_BG, outline=""
        )
        self._text_id = self.create_text(
            100,
            15,
            text=f"{name} {variable.get()}",
            fill="white",
            angle=90 if orient == tk.VERTICAL else 0,
        )

        self.bind("<Configure>", lambda event: self._redraw())
        self._variable.trace_add("write", lambda *_: self._redraw())

    def _redraw(self) -> None:
        value = self._variable.get()

        fraction = (value - self._minimum) / (self._maximum - self._minimum)
        fraction = max(0.0, min(1.0, fraction))

        width, height = self.winfo_width(), self.winfo_height()

        if self._orient == tk.HORIZONTAL:
            self.coords(self._fill_id, 0, 0, width * fraction, height)
        else:
            self.coords(self._fill_id, 0, height * (1 - fraction), width, height)

        self.coords(self._text_id, width / 2, height / 2)

        self.itemconfigure(self._text_id, text=f"{self._name} {value}")
