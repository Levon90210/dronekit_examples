import os
import tkinter as tk

from tkintermapview import TkinterMapView

root = tk.Tk()
root.title("Map test")
root.geometry("900x600")

map_widget = TkinterMapView(root, corner_radius=0)
map_widget.set_tile_server(
    "https://api.maptiler.com/maps/streets-v4/256/{z}/{x}/{y}.png"
    f"?key={os.environ['MAPTILER_API_KEY']}",
    max_zoom=19,
)
map_widget.pack(fill="both", expand=True)

map_widget.set_position(40.18, 44.51)
map_widget.set_zoom(15)

tk.Label(root, text="© OpenStreetMap contributors").pack(anchor="e")

root.mainloop()
