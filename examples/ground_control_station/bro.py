import collections
import collections.abc
collections.MutableMapping = collections.abc.MutableMapping

import tkinter as tk
from tkinter import messagebox
import threading
import math

from dronekit import connect, VehicleMode
from tkintermapview import TkinterMapView


class GroundControlStation:
    def __init__(self, root):
        self.root = root
        self.root.title("Ground Control Station")
        self.root.geometry("1050x820")
        self.root.minsize(850, 750)
        self.root.configure(bg="#252A27")

        self.vehicle = None
        self.connecting = False
        self.running = True

        self.roll = 1500
        self.pitch = 1500
        self.throttle = 1000
        self.yaw = 1500

        self.pressed_keys = set()
        self.rc_bars = {}
        self.rc_labels = {}

        self.drone_marker = None
        self.heading_line = None
        self.follow_drone = tk.BooleanVar(value=True)

        self.create_widgets()

        self.root.bind_all("<KeyPress>", self.key_press)
        self.root.bind_all("<KeyRelease>", self.key_release)
        self.root.bind("<FocusOut>", self.focus_lost)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.focus_set()

        self.update_status()
        self.update_rc()
        self.update_map()

    def create_widgets(self):
        left = tk.Frame(self.root, bg="#252A27", width=420)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        map_frame = tk.Frame(self.root, bg="#252A27")
        map_frame.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)

        conn_frame = tk.LabelFrame(
            left, text="Connection Settings",
            padx=10, pady=10, bg="#252A27", fg="white"
        )
        conn_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(
            conn_frame, text="Connection String:",
            bg="#252A27", fg="white"
        ).pack(anchor="w")

        self.conn_entry = tk.Entry(conn_frame)
        self.conn_entry.insert(0, "127.0.0.1:14550")
        self.conn_entry.pack(fill="x", pady=5)

        btn_frame = tk.Frame(conn_frame, bg="#252A27")
        btn_frame.pack(fill="x", pady=5)

        tk.Button(
            btn_frame, text="Connect",
            command=self.connect_vehicle,
            bg="#C8E6C9", fg="#1B4332"
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        tk.Button(
            btn_frame, text="Close Connection",
            command=self.close_connection,
            bg="#2D6A4F", fg="white"
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))

        state_frame = tk.LabelFrame(
            left, text="Current State",
            padx=10, pady=10, bg="#252A27", fg="white"
        )
        state_frame.pack(fill="x", padx=15, pady=5)

        self.connection_label = tk.Label(
            state_frame, text="Connected: No",
            bg="#252A27", fg="white", anchor="w"
        )
        self.connection_label.pack(fill="x")

        self.mode_label = tk.Label(
            state_frame, text="Mode: -",
            bg="#252A27", fg="white", anchor="w"
        )
        self.mode_label.pack(fill="x")

        self.armed_label = tk.Label(
            state_frame, text="Armed: No",
            bg="#252A27", fg="white", anchor="w"
        )
        self.armed_label.pack(fill="x")

        self.altitude_label = tk.Label(
            state_frame, text="Altitude: 0.00 m",
            bg="#252A27", fg="white", anchor="w"
        )
        self.altitude_label.pack(fill="x")

        control_frame = tk.LabelFrame(
            left, text="Flight Controls",
            padx=10, pady=10, bg="#252A27", fg="white"
        )
        control_frame.pack(fill="x", padx=15, pady=5)

        tk.Button(
            control_frame, text="Arm",
            command=self.arm_vehicle,
            bg="#FFF0B3", fg="#5D4E00"
        ).pack(fill="x", pady=5)

        takeoff_frame = tk.Frame(control_frame, bg="#252A27")
        takeoff_frame.pack(fill="x", pady=5)

        tk.Label(
            takeoff_frame, text="Takeoff Altitude (m):",
            bg="#252A27", fg="white"
        ).pack(side="left")

        self.altitude_entry = tk.Entry(takeoff_frame, width=8)
        self.altitude_entry.insert(0, "5")
        self.altitude_entry.pack(side="left", padx=5)

        tk.Button(
            control_frame, text="Takeoff",
            command=self.takeoff_vehicle,
            bg="#C8E6C9", fg="#1B4332"
        ).pack(fill="x", pady=5)

        tk.Label(
            control_frame, text="Flight Modes:",
            bg="#252A27", fg="white"
        ).pack(anchor="w", pady=5)

        for mode in ["GUIDED", "STABILIZE", "LOITER", "LAND", "RTL"]:
            tk.Button(
                control_frame, text=mode,
                command=lambda m=mode: self.change_mode(m),
                bg="#E8ECE9", fg="#333333"
            ).pack(fill="x", pady=2)

        rc_frame = tk.LabelFrame(
            left, text="RC Channels",
            padx=10, pady=10, bg="#252A27", fg="white"
        )
        rc_frame.pack(fill="x", padx=15, pady=5)

        for channel, name in [
            (1, "Roll"),
            (2, "Pitch"),
            (3, "Throttle"),
            (4, "Yaw")
        ]:
            frame = tk.Frame(rc_frame, bg="#252A27")
            frame.pack(fill="x", pady=3)

            tk.Label(
                frame, text=f"CH{channel} {name}",
                width=12, anchor="w",
                bg="#252A27", fg="white"
            ).pack(side="left")

            canvas = tk.Canvas(
                frame, width=170, height=18,
                bg="#444444", highlightthickness=0
            )
            canvas.pack(side="left", padx=5)

            label = tk.Label(
                frame, text="1500", width=5,
                bg="#252A27", fg="white"
            )
            label.pack(side="left")

            self.rc_bars[channel] = canvas
            self.rc_labels[channel] = label

        tk.Label(
            rc_frame,
            text="W/S - Throttle | A/D - Yaw\n"
                 "Left/Right - Roll | Up/Down - Pitch",
            bg="#252A27", fg="white"
        ).pack(pady=5)

        self.status_label = tk.Label(
            left, text="Status: Disconnected",
            bg="#252A27", fg="white", anchor="w"
        )
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

        map_top = tk.Frame(map_frame, bg="#252A27")
        map_top.pack(fill="x", pady=(0, 5))

        tk.Label(
            map_top, text="Drone Map", bg="#252A27",
            fg="white", font=("Arial", 13, "bold")
        ).pack(side="left")

        tk.Checkbutton(
            map_top, text="Follow drone", variable=self.follow_drone,
            bg="#252A27", fg="white", selectcolor="#252A27",
            activebackground="#252A27", activeforeground="white"
        ).pack(side="right")

        self.map_widget = TkinterMapView(map_frame, corner_radius=0)
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_position(40.18, 44.51)  # Initial view (Yerevan)
        self.map_widget.set_zoom(15)

        self.map_label = tk.Label(
            map_frame, text="Waiting for drone GPS...",
            bg="#252A27", fg="white", anchor="w"
        )
        self.map_label.pack(fill="x", pady=(5, 0))

    def is_connected(self):
        if self.vehicle is None:
            return False

        try:
            return self.vehicle.last_heartbeat < 5
        except Exception:
            return False

    def connect_vehicle(self):
        if self.vehicle is not None or self.connecting:
            return

        conn_string = self.conn_entry.get().strip()
        self.connecting = True
        self.status_label.config(text="Status: Connecting...")

        def task():
            try:
                vehicle = connect(conn_string, wait_ready=True, timeout=30)
                if self.running:
                    self.root.after(0, lambda: self.connection_success(vehicle))
                else:
                    vehicle.close()
            except Exception as e:
                error = str(e)
                if self.running:
                    self.root.after(0, lambda: self.connection_error(error))

        threading.Thread(target=task, daemon=True).start()

    def connection_success(self, vehicle):
        self.vehicle = vehicle
        self.connecting = False
        self.status_label.config(text="Status: Connected")
        self.root.focus_set()

    def connection_error(self, error):
        self.connecting = False
        self.status_label.config(text="Status: Connection Failed")
        messagebox.showerror("Error", error)

    def clear_map(self):
        if self.drone_marker is not None:
            self.drone_marker.delete()
            self.drone_marker = None
        if self.heading_line is not None:
            self.heading_line.delete()
            self.heading_line = None
        self.map_label.config(text="Waiting for drone GPS...")

    def close_connection(self):
        if self.vehicle is None:
            messagebox.showwarning("Warning", "No active connection")
            return

        try:
            self.pressed_keys.clear()
            self.vehicle.channels.overrides = {}
            self.vehicle.close()
            self.vehicle = None

            self.roll = 1500
            self.pitch = 1500
            self.throttle = 1000
            self.yaw = 1500

            self.clear_map()
            self.status_label.config(text="Status: Disconnected")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def arm_vehicle(self):
        if not self.is_connected():
            messagebox.showwarning("Warning", "Connect first!")
            return

        try:
            self.vehicle.armed = True
            self.status_label.config(text="Status: Arming...")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def change_mode(self, mode):
        if not self.is_connected():
            messagebox.showwarning("Warning", "Connect first!")
            return

        try:
            self.pressed_keys.clear()
            self.vehicle.channels.overrides = {}
            self.vehicle.mode = VehicleMode(mode)
            self.status_label.config(text=f"Status: Mode -> {mode}")
            self.root.focus_set()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def takeoff_vehicle(self):
        if not self.is_connected():
            messagebox.showwarning("Warning", "Connect first!")
            return

        try:
            altitude = float(self.altitude_entry.get())

            if altitude <= 0:
                messagebox.showwarning("Warning", "Altitude must be greater than 0")
                return

            if self.vehicle.mode.name != "GUIDED":
                messagebox.showwarning("Warning", "Switch to GUIDED mode first!")
                return

            if not self.vehicle.armed:
                messagebox.showwarning("Warning", "Arm the drone first!")
                return

            self.pressed_keys.clear()
            self.vehicle.channels.overrides = {}
            self.vehicle.simple_takeoff(altitude)
            self.status_label.config(text=f"Status: Taking off to {altitude} m")
            self.root.focus_set()

        except ValueError:
            messagebox.showerror("Error", "Invalid altitude")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def key_press(self, event):
        key = event.keysym.lower()
        keys = ["w", "s", "a", "d", "left", "right", "up", "down"]

        if key not in keys:
            return
        if isinstance(self.root.focus_get(), tk.Entry):
            return

        if self.is_connected():
            self.pressed_keys.add(key)
        return "break"

    def key_release(self, event):
        key = event.keysym.lower()
        self.pressed_keys.discard(key)

        if key in ["w", "s", "a", "d", "left", "right", "up", "down"]:
            if not isinstance(self.root.focus_get(), tk.Entry):
                return "break"

    def focus_lost(self, event):
        if event.widget == self.root:
            self.pressed_keys.clear()

    def update_rc(self):
        if self.is_connected():
            try:
                mode = self.vehicle.mode.name

                if mode in ["LOITER", "STABILIZE"]:
                    self.roll = 1500
                    self.pitch = 1500
                    self.yaw = 1500

                    if mode == "LOITER":
                        self.throttle = 1500
                    else:
                        self.throttle = 1000

                    if "left" in self.pressed_keys:
                        self.roll = 1400
                    if "right" in self.pressed_keys:
                        self.roll = 1600

                    if "up" in self.pressed_keys:
                        self.pitch = 1400
                    if "down" in self.pressed_keys:
                        self.pitch = 1600

                    if "a" in self.pressed_keys:
                        self.yaw = 1400
                    if "d" in self.pressed_keys:
                        self.yaw = 1600

                    if "w" in self.pressed_keys:
                        self.throttle = 1600
                    if "s" in self.pressed_keys:
                        self.throttle = 1400

                    overrides = {
                        "1": self.roll,
                        "2": self.pitch,
                        "4": self.yaw
                    }

                    if mode == "LOITER":
                        overrides["3"] = self.throttle
                    elif "w" in self.pressed_keys or "s" in self.pressed_keys:
                        overrides["3"] = self.throttle

                    self.vehicle.channels.overrides = overrides
                else:
                    self.pressed_keys.clear()
                    self.vehicle.channels.overrides = {}
                    self.roll = 1500
                    self.pitch = 1500
                    self.throttle = 1000
                    self.yaw = 1500

            except Exception as e:
                print("RC Error:", e)

        self.draw_rc(1, self.roll)
        self.draw_rc(2, self.pitch)
        self.draw_rc(3, self.throttle)
        self.draw_rc(4, self.yaw)

        if self.running:
            self.root.after(100, self.update_rc)

    def draw_rc(self, channel, value):
        canvas = self.rc_bars[channel]
        canvas.delete("all")

        position = (value - 1000) / 1000 * 170
        position = max(0, min(170, position))

        canvas.create_rectangle(0, 0, position, 18, fill="#81C784", outline="")
        canvas.create_line(85, 0, 85, 18, fill="white", dash=(2, 2))
        self.rc_labels[channel].config(text=str(value))

    def update_status(self):
        if self.is_connected():
            try:
                mode = self.vehicle.mode.name
                armed = self.vehicle.armed
                altitude = self.vehicle.location.global_relative_frame.alt

                if altitude is None:
                    altitude = 0

                self.connection_label.config(text="Connected: Yes", fg="#81C784")
                self.mode_label.config(text=f"Mode: {mode}")
                self.armed_label.config(text=f"Armed: {'Yes' if armed else 'No'}")
                self.altitude_label.config(text=f"Altitude: {altitude:.2f} m")
            except Exception:
                pass
        else:
            self.connection_label.config(text="Connected: No", fg="white")
            self.mode_label.config(text="Mode: -")
            self.armed_label.config(text="Armed: No")
            self.altitude_label.config(text="Altitude: 0.00 m")

        if self.running:
            self.root.after(500, self.update_status)

    def update_map(self):
        if self.is_connected():
            try:
                pos = self.vehicle.location.global_frame
                yaw = self.vehicle.attitude.yaw

                if pos.lat is not None and pos.lon is not None:
                    lat, lon = pos.lat, pos.lon
                    if self.drone_marker is None:
                        self.drone_marker = self.map_widget.set_marker(lat, lon, text="Drone")
                    else:
                        self.drone_marker.set_position(lat, lon)

                    if yaw is not None:
                        end_lat = lat + 20 * math.cos(yaw) / 111320
                        end_lon = lon + 20 * math.sin(yaw) / (111320 * max(0.01, math.cos(math.radians(lat))))
                        if self.heading_line is not None:
                            self.heading_line.delete()
                        self.heading_line = self.map_widget.set_path(
                            [(lat, lon), (end_lat, end_lon)], color="green", width=5
                        )

                    if self.follow_drone.get():
                        self.map_widget.set_position(lat, lon)

                    angle = f"{math.degrees(yaw) % 360:.0f}°" if yaw is not None else "-"
                    self.map_label.config(text=f"Lat: {lat:.6f}  Lon: {lon:.6f}  Yaw: {angle}")
            except Exception as e:
                print("Map error:", e)
        elif self.drone_marker is not None:
            self.clear_map()

        if self.running:
            self.root.after(500, self.update_map)

    def on_close(self):
        self.running = False
        self.pressed_keys.clear()

        if self.vehicle is not None:
            try:
                self.vehicle.channels.overrides = {}
                self.vehicle.close()
            except Exception:
                pass

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = GroundControlStation(root)
    root.mainloop()

