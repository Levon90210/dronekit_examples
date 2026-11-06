import queue
import threading
import tkinter as tk
from typing import Any, Optional

import config
from connection_panel import ConnectionPanel
from flight_modes_panel import FlightModesPanel
from keyboard_rc_input import KeyboardRCInput
from logs_panel import LogsPanel
from rc_channel_indicator import RCChannelIndicator
from rc_controls_panel import RCControlsPanel
from vehicle_panel import VehiclePanel
import theme
from vehicle_controller import VehicleController


class GroundControlStation:
    def __init__(self) -> None:
        self._root = tk.Tk()
        self._initialize_root_window()

        self._controller = VehicleController()
        self._keyboard_input = KeyboardRCInput()

        self._keyboard_control_enabled = False
        self._connecting = False
        self._connection_results: queue.Queue[tuple[bool, Optional[Exception]]] = (
            queue.Queue()
        )
        self._pressed_keys: set[str] = set()
        self._previous_mode_name: Optional[str] = None

        self._main_panel = tk.Frame(self._root, bg=theme.WINDOW_BG)
        self._main_panel.grid(row=0, column=0, sticky="nsew")

        self._root.rowconfigure(0, weight=1)
        self._root.columnconfigure(0, weight=2)
        self._root.columnconfigure(1, weight=1)

        self._create_connection_section()
        self._create_flight_mode_section()
        self._create_vehicle_section()
        self._create_logs_section()
        self._create_rc_controls_section()

        self._root.bind("<KeyPress>", self._on_key_press)
        self._root.bind("<KeyRelease>", self._on_key_release)
        self._root.bind("<FocusOut>", self._on_focus_out)

        self._append_log("GCS started")
        self._refresh_vehicle_state()
        self._update_rc_inputs()

    def run(self) -> None:
        self._root.mainloop()

    def _create_connection_section(self) -> None:
        self._connection_panel = ConnectionPanel(
            self._main_panel,
            on_connect=self._connect_vehicle,
            on_disconnect=self._close_connection,
        )
        self._connection_panel.pack(fill="x", padx=15, pady=10)

    def _create_flight_mode_section(self) -> None:
        self._flight_modes_panel = FlightModesPanel(
            self._main_panel, on_mode_selected=self._set_mode
        )
        self._flight_modes_panel.pack(fill="x", padx=15, pady=10)

    def _create_vehicle_section(self) -> None:
        self._vehicle_panel = VehiclePanel(
            self._main_panel,
            on_arm=self._arm_vehicle,
            on_takeoff=self._takeoff_vehicle,
        )
        self._vehicle_panel.pack(fill="x", padx=15, pady=10)

    def _create_logs_section(self) -> None:
        self._logs_panel = LogsPanel(self._main_panel)
        self._logs_panel.pack(fill="both", expand=True, padx=15, pady=10)

    def _create_rc_controls_section(self) -> None:
        self._rc_controls_panel = RCControlsPanel(
            self._root, on_keyboard_toggle=self._on_keyboard_control_changed
        )
        self._rc_controls_panel.grid(row=0, column=1, sticky="nsew", padx=15, pady=10)

    def _refresh_vehicle_state(self) -> None:
        mode_name = self._controller.mode_name

        mode_changed = mode_name != self._previous_mode_name
        can_control_rc = self._controller.can_control_rc

        self._previous_mode_name = mode_name

        self._rc_controls_panel.set_keyboard_available(can_control_rc)

        if self._keyboard_control_enabled and (mode_changed or not can_control_rc):
            self._on_keyboard_control_changed(False)

        self._flight_modes_panel.set_mode(mode_name)

        self._vehicle_panel.set_arm_available(self._controller.can_arm)
        self._vehicle_panel.set_takeoff_available(
            mode_name == "GUIDED" and self._controller.armed
        )
        self._vehicle_panel.set_altitude(self._controller.relative_altitude)

        for message in self._controller.drain_log_messages():
            self._append_log(f"AUTOPILOT: {message}")

        self._root.after(config.VEHICLE_REFRESH_MS, self._refresh_vehicle_state)

    def _update_rc_inputs(self) -> None:
        self._keyboard_input.update(pressed_keys=self._pressed_keys)
        values = self._keyboard_input.values

        self._rc_controls_panel.set_values(values)

        if self._keyboard_control_enabled:
            try:
                self._controller.set_rc_inputs(**values)

            except Exception as error:
                self._append_log(f"ERROR: {error}")
                self._on_keyboard_control_changed(False)

        self._root.after(config.RC_UPDATE_MS, self._update_rc_inputs)

    def _connect_vehicle(self) -> None:
        connection_string = self._connection_panel.get_connection_string()
        if not connection_string:
            return

        self._connection_panel.set_status("Connecting...")
        self._connecting = True
        self._append_log("Connecting...")

        self._connection_panel.set_controls(connecting=True, connected=False)
        threading.Thread(
            target=self._connection_worker, args=(connection_string,)
        ).start()
        self._root.after(config.CONNECTION_POLL_MS, self._check_connection_result)

    def _close_connection(self) -> bool:
        try:
            if self._keyboard_control_enabled:
                self._on_keyboard_control_changed(False)

            self._controller.disconnect()

            self._connection_panel.set_status("Disconnected")
            self._set_connection_controls(connected=False)
            self._append_log("Disconnected")
            return True

        except Exception as error:
            self._append_log(f"ERROR: {error}")
            return False

    def _set_mode(self, mode_name: str) -> None:
        try:
            self._append_log(f"Requested mode: {mode_name}")
            self._controller.set_mode(mode_name)
        except Exception as error:
            self._append_log(f"ERROR: {error}")

    def _arm_vehicle(self) -> None:
        try:
            self._append_log("Arm requested")
            self._controller.arm()
        except Exception as error:
            self._append_log(f"ERROR: {error}")

    def _takeoff_vehicle(self) -> None:
        target_altitude = self._vehicle_panel.get_target_altitude()
        if not target_altitude:
            return

        try:
            self._append_log(f"Takeoff requested: {target_altitude} m")
            self._controller.takeoff(float(target_altitude))
        except Exception as error:
            self._append_log(f"ERROR: {error}")

    def _connection_worker(self, connection_string: str) -> None:
        try:
            self._controller.connect(connection_string)
            self._connection_results.put((True, None))

        except Exception as error:
            self._connection_results.put((False, error))

    def _check_connection_result(self) -> None:
        try:
            success, error = self._connection_results.get_nowait()
            self._connecting = False

            if success:
                self._connection_panel.set_status("Connected")
                self._set_connection_controls(connected=True)
                self._append_log("Connected")

            else:
                self._connection_panel.set_status("Connection failed")
                self._set_connection_controls(connected=False)
                self._append_log(f"ERROR: {error}")

        except queue.Empty:
            self._root.after(config.CONNECTION_POLL_MS, self._check_connection_result)

    def _set_connection_controls(self, *, connected: bool) -> None:
        self._connection_panel.set_controls(
            connecting=self._connecting,
            connected=connected,
        )
        self._flight_modes_panel.set_available(connected)

    def _append_log(self, message: str) -> None:
        self._logs_panel.append(message)

    def _initialize_root_window(self) -> None:
        self._root.title("Trust Me, It Flies")
        self._root.geometry(f"{config.ROOT_WINDOW_WIDTH}x{config.ROOT_WINDOW_HEIGHT}")
        self._root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        self._root.configure(bg=theme.WINDOW_BG)
        self._root.option_add("*Font", ("Arial", 11))

    def _on_key_press(self, event: tk.Event) -> None:
        if (
            isinstance(event.widget, (tk.Entry, tk.Text))
            or not self._keyboard_control_enabled
        ):
            return

        key = event.keysym.lower()
        if key in {"w", "s", "a", "d", "left", "right", "up", "down"}:
            self._pressed_keys.add(key)

    def _on_key_release(self, event: tk.Event) -> None:
        key = event.keysym.lower()
        if key in {"w", "s", "a", "d", "left", "right", "up", "down"}:
            self._pressed_keys.discard(key)

    def _on_focus_out(self, event: tk.Event) -> None:
        self._pressed_keys.clear()
        self._root.after_idle(self._check_control_focus)

    def _on_keyboard_control_changed(self, enabled: bool) -> None:
        self._pressed_keys.clear()

        if enabled:
            mode_name = self._controller.mode_name

            if not self._controller.can_control_rc:
                self._rc_controls_panel.set_keyboard_enabled(False)
                self._append_log("Keyboard control requires STABILIZE or LOITER")
                return

            if mode_name == "STABILIZE" and self._controller.armed:
                self._rc_controls_panel.set_keyboard_enabled(False)
                self._append_log("Enable keyboard control before arming in STABILIZE")
                return

            throttle = (
                config.RC_CENTER
                if mode_name == "LOITER" and self._controller.armed
                else config.RC_MIN
            )
            self._keyboard_input.reset(throttle=throttle)

        self._keyboard_control_enabled = enabled
        self._rc_controls_panel.set_keyboard_enabled(enabled)

        if not enabled:
            try:
                self._controller.release_rc_inputs()
            except Exception as error:
                self._append_log(f"ERROR: {error}")

    def _on_window_close(self) -> None:
        if self._connecting:
            print("Wait for the connection attempt to finish")
        else:
            if self._close_connection():
                self._root.destroy()

    def _check_control_focus(self) -> None:
        focused_widget = self._root.focus_get()
        if focused_widget is None or isinstance(focused_widget, (tk.Entry, tk.Text)):
            if self._keyboard_control_enabled:
                self._on_keyboard_control_changed(False)


def main() -> None:
    gcs = GroundControlStation()
    gcs.run()


if __name__ == "__main__":
    main()
