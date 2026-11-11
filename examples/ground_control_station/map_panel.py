import os
import tkinter as tk
from typing import Optional
import webbrowser

from tkintermapview import TkinterMapView
from tkintermapview.map_widget import CanvasPositionMarker

import theme


class MapPanel(tk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)

        self._map_widget = TkinterMapView(self, width=700, height=500, corner_radius=0)
        self._map_widget.set_tile_server(
            "https://api.maptiler.com/maps/streets-v4/256/{z}/{x}/{y}.png"
            f"?key={os.environ['MAPTILER_API_KEY']}",
            max_zoom=19,
        )
        self._map_widget.pack(fill="both", expand=True)
        self._map_widget.set_position(40.18, 44.51)
        self._map_widget.set_zoom(17)

        self._attribution_frame = tk.Frame(self._map_widget, bg=theme.WHITE)
        self._attribution_frame.place(relx=1, rely=1, anchor="se", x=-8, y=-8)

        self._maptiler_attribution_label = tk.Label(
            self._attribution_frame,
            text="© MapTiler",
            bg=theme.WHITE,
            fg=theme.BLACK,
            cursor="hand2",
        )
        self._maptiler_attribution_label.pack(side="left", padx=4)
        self._maptiler_attribution_label.bind(
            "<Button-1>",
            lambda event: self._on_label_click(
                event, "https://www.maptiler.com/copyright/"
            ),
        )

        self._osm_attribution_label = tk.Label(
            self._attribution_frame,
            text="© OpenStreetMap contributors",
            bg=theme.WHITE,
            fg=theme.BLACK,
            cursor="hand2",
        )
        self._osm_attribution_label.pack(side="left", padx=4)
        self._osm_attribution_label.bind(
            "<Button-1>",
            lambda event: self._on_label_click(
                event, "https://www.openstreetmap.org/copyright"
            ),
        )

        self._drone_marker: Optional[CanvasPositionMarker] = None
        self._home_marker: Optional[CanvasPositionMarker] = None

        self._follow_drone_var = tk.BooleanVar(value=True)
        self._follow_drone_btn = tk.Checkbutton(
            self,
            text="Follow drone",
            variable=self._follow_drone_var,
            command=self._on_follow_drone_toggle,
        )
        self._follow_drone_btn.pack(anchor="w")

        self._last_position: Optional[tuple[float, float]] = None
        self._last_home_position: Optional[tuple[float, float]] = None

    def set_position(self, position: Optional[tuple[float, float]]) -> None:
        if self._last_position == position:
            return

        self._last_position = position
        if position is None:
            if self._drone_marker is not None:
                self._drone_marker.delete()
                self._drone_marker = None
            return

        latitude, longitude = position

        if self._drone_marker is None:
            self._drone_marker = self._map_widget.set_marker(
                latitude, longitude, text="Drone"
            )
        else:
            self._drone_marker.set_position(latitude, longitude)

        if self._follow_drone_var.get():
            self._map_widget.set_position(latitude, longitude)

    def set_home_position(self, position: Optional[tuple[float, float]]) -> None:
        if self._last_home_position == position:
            return

        self._last_home_position = position
        if position is None:
            if self._home_marker is not None:
                self._home_marker.delete()
                self._home_marker = None
            return

        latitude, longitude = position

        if self._home_marker is None:
            self._home_marker = self._map_widget.set_marker(
                latitude, longitude, text="Home"
            )
        else:
            self._home_marker.set_position(latitude, longitude)

    def _on_follow_drone_toggle(self) -> None:
        if (
            self._follow_drone_var.get()
            and self._drone_marker is not None
            and self._last_position is not None
        ):
            latitude, longitude = self._last_position
            self._map_widget.set_position(latitude, longitude)

    def _on_label_click(self, event: tk.Event, url: str) -> None:
        webbrowser.open_new_tab(url)
