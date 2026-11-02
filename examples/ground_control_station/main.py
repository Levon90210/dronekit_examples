import queue
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from typing import Any, Optional

from constants import *
from rc_channel_indicator import RCChannelIndicator
from vehicle_controller import VehicleController


class GroundControlStation:
    def __init__(self) -> None:
        self._root = tk.Tk()
        self._initialize_root_window()

        self._controller = VehicleController()
        self._connecting = False
        self._connection_results: queue.Queue[tuple[bool, Optional[Exception]]] = (
            queue.Queue()
        )
        self._pressed_keys: set[str] = set()
        self._previous_mode_name: Optional[str] = None

        self._main_panel = tk.Frame(self._root, bg=WINDOW_BG)
        self._rc_panel = tk.Frame(self._root, bg=WINDOW_BG)
        self._main_panel.grid(row=0, column=0, sticky="nsew")
        self._rc_panel.grid(row=0, column=1, sticky="nsew")
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
        self._connection_frame = self._create_section_frame(
            self._main_panel, title="Connection"
        )
        self._connection_label = tk.Label(
            self._connection_frame,
            text="Disconnected",
            bg=SECTION_BG,
            fg=SECONDARY_TEXT_COLOR,
        )
        self._connection_string_label = tk.Label(
            self._connection_frame,
            text="Connection string",
            bg=SECTION_BG,
            fg=MAIN_TEXT_COLOR,
        )
        self._connection_entry = tk.Entry(
            self._connection_frame,
            bg=INPUT_BG,
            fg=MAIN_TEXT_COLOR,
            insertbackground=MAIN_TEXT_COLOR,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=SECONDARY_TEXT_COLOR,
            highlightcolor=PRIMARY_BG,
        )
        self._connection_entry.insert(0, "127.0.0.1:14550")
        self._connection_buttons_frame = tk.Frame(self._connection_frame, bg=SECTION_BG)
        self._connect_btn = tk.Button(
            self._connection_buttons_frame,
            text="Connect",
            command=self._connect_vehicle,
            **BUTTON_DEFAULTS,
            **PRIMARY_BUTTON_STYLE,
        )
        self._close_connection_btn = tk.Button(
            self._connection_buttons_frame,
            text="Close Connection",
            command=self._close_connection,
            state=tk.DISABLED,
            **BUTTON_DEFAULTS,
            **SECONDARY_BUTTON_STYLE,
        )
        self._layout_connection_widgets()

    def _create_flight_mode_section(self) -> None:
        self._flight_mode_frame = self._create_section_frame(
            self._main_panel, title="Flight modes"
        )
        self._current_mode_label = tk.Label(
            self._flight_mode_frame,
            text="Current mode: -",
            bg=SECTION_BG,
            fg=MAIN_TEXT_COLOR,
        )
        self._mode_btn_map = {
            mode: tk.Button(
                self._flight_mode_frame,
                text=mode,
                command=lambda mode=mode: self._set_mode(mode),
                state=tk.DISABLED,
                **BUTTON_DEFAULTS,
                **SECONDARY_BUTTON_STYLE,
            )
            for mode in MODE_LIST
        }
        self._layout_flight_mode_widgets()

    def _create_vehicle_section(self) -> None:
        self._vehicle_frame = self._create_section_frame(
            self._main_panel, title="Vehicle"
        )
        self._arm_btn = tk.Button(
            self._vehicle_frame,
            text="Arm",
            command=self._arm_vehicle,
            state=tk.DISABLED,
            **BUTTON_DEFAULTS,
            **{**ARM_BUTTON_STYLE, "bg": ARM_DISABLED_BG},
        )
        self._takeoff_controls_frame = tk.Frame(self._vehicle_frame, bg=SECTION_BG)
        self._target_altitude_label = tk.Label(
            self._takeoff_controls_frame,
            text="Target altitude (m)",
            bg=SECTION_BG,
            fg=MAIN_TEXT_COLOR,
        )
        self._target_altitude_entry = tk.Entry(
            self._takeoff_controls_frame,
            bg=INPUT_BG,
            fg=MAIN_TEXT_COLOR,
            insertbackground=MAIN_TEXT_COLOR,
            relief=tk.FLAT,
            bd=0,
            width=8,
            highlightthickness=1,
            highlightbackground=SECONDARY_TEXT_COLOR,
            highlightcolor=PRIMARY_BG,
        )
        self._takeoff_btn = tk.Button(
            self._takeoff_controls_frame,
            text="Takeoff",
            command=self._takeoff_vehicle,
            state=tk.DISABLED,
            **BUTTON_DEFAULTS,
            **{**ARM_BUTTON_STYLE, "bg": ARM_DISABLED_BG},
        )
        self._current_altitude_label = tk.Label(
            self._vehicle_frame, text="Altitude: -", bg=SECTION_BG, fg=MAIN_TEXT_COLOR
        )
        self._layout_vehicle_widgets()

    def _create_logs_section(self) -> None:
        self._logs_frame = self._create_section_frame(self._main_panel, title="Logs")
        self._logs_area = ScrolledText(
            self._logs_frame, state=tk.DISABLED, **LOG_AREA_STYLE
        )
        self._layout_logs_widgets()

    def _create_rc_controls_section(self) -> None:
        self._rc_controls_frame = self._create_section_frame(
            self._rc_panel, title="RC Controls"
        )
        self._rc_values: dict[str, tk.IntVar] = {
            "roll": tk.IntVar(master=self._root, value=RC_CENTER),
            "pitch": tk.IntVar(master=self._root, value=RC_CENTER),
            "throttle": tk.IntVar(master=self._root, value=RC_MIN),
            "yaw": tk.IntVar(master=self._root, value=RC_CENTER),
        }
        self._roll_indicator = RCChannelIndicator(
            self._rc_controls_frame,
            name="Roll",
            variable=self._rc_values["roll"],
            orient=tk.HORIZONTAL,
        )
        self._pitch_indicator = RCChannelIndicator(
            self._rc_controls_frame,
            name="Pitch",
            variable=self._rc_values["pitch"],
            orient=tk.VERTICAL,
        )
        self._throttle_indicator = RCChannelIndicator(
            self._rc_controls_frame,
            name="Throttle",
            variable=self._rc_values["throttle"],
            orient=tk.VERTICAL,
        )
        self._yaw_indicator = RCChannelIndicator(
            self._rc_controls_frame,
            name="Yaw",
            variable=self._rc_values["yaw"],
            orient=tk.HORIZONTAL,
        )
        for widget in (
            self._rc_controls_frame,
            self._roll_indicator,
            self._pitch_indicator,
            self._throttle_indicator,
            self._yaw_indicator,
        ):
            widget.bind("<Button-1>", self._focus_rc_controls)

        self._keyboard_enabled = tk.BooleanVar(self._root, value=False)
        self._keyboard_control_btn = tk.Checkbutton(
            self._rc_controls_frame,
            text="Enable keyboard control",
            variable=self._keyboard_enabled,
            command=self._on_keyboard_control_changed,
            bg=SECTION_BG,
            fg=MAIN_TEXT_COLOR,
            selectcolor=INPUT_BG,
            activebackground=SECTION_BG,
            activeforeground=MAIN_TEXT_COLOR,
        )
        self._keyboard_control_status_label = tk.Label(
            self._rc_controls_frame,
            text="Keyboard control: OFF",
            bg=SECTION_BG,
            fg=MAIN_TEXT_COLOR,
        )
        self._layout_rc_controls_widgets()

    def _refresh_vehicle_state(self) -> None:
        mode_name = self._controller.mode_name

        mode_changed = mode_name != self._previous_mode_name
        can_control_rc = self._controller.can_control_rc

        if self._keyboard_enabled.get() and (mode_changed or not can_control_rc):
            self._keyboard_enabled.set(False)
            self._on_keyboard_control_changed()

        self._previous_mode_name = mode_name

        if mode_name is None:
            self._current_mode_label.config(text="Current mode: -")

        else:
            self._current_mode_label.config(text=f"Current mode: {mode_name}")

        can_arm = self._controller.can_arm
        desired_arm_state = tk.NORMAL if can_arm else tk.DISABLED

        if self._arm_btn.cget("state") != desired_arm_state:
            self._arm_btn.config(
                state=desired_arm_state,
                bg=ARM_BG if can_arm else ARM_DISABLED_BG,
            )

        can_takeoff = mode_name == "GUIDED" and self._controller.armed
        desired_takeoff_state = tk.NORMAL if can_takeoff else tk.DISABLED

        if self._takeoff_btn.cget("state") != desired_takeoff_state:
            self._takeoff_btn.config(
                state=desired_takeoff_state,
                bg=ARM_BG if can_takeoff else ARM_DISABLED_BG,
            )

        desired_keyboard_control_state = tk.NORMAL if can_control_rc else tk.DISABLED

        if self._keyboard_control_btn.cget("state") != desired_keyboard_control_state:
            self._keyboard_control_btn.config(state=desired_keyboard_control_state)

        altitude = self._controller.relative_altitude
        if altitude is None:
            self._current_altitude_label.config(text="Altitude: -")

        else:
            self._current_altitude_label.config(text=f"Altitude: {altitude:.1f} m")

        for message in self._controller.drain_log_messages():
            self._append_log(f"AUTOPILOT: {message}")

        self._root.after(200, self._refresh_vehicle_state)

    def _update_rc_inputs(self) -> None:
        roll_direction = int("right" in self._pressed_keys) - int(
            "left" in self._pressed_keys
        )
        if roll_direction != 0:
            self._rc_values["roll"].set(
                max(
                    RC_MIN, min(RC_MAX, self._rc_values["roll"].get() + 25 * roll_direction)
                )
            )
        else:
            self._rc_values["roll"].set(RC_CENTER)

        pitch_direction = int("down" in self._pressed_keys) - int(
            "up" in self._pressed_keys
        )
        if pitch_direction:
            self._rc_values["pitch"].set(
                max(
                    RC_MIN,
                    min(RC_MAX, self._rc_values["pitch"].get() + 25 * pitch_direction),
                )
            )
        else:
            self._rc_values["pitch"].set(RC_CENTER)

        yaw_direction = int("d" in self._pressed_keys) - int("a" in self._pressed_keys)
        if yaw_direction:
            self._rc_values["yaw"].set(
                max(RC_MIN, min(RC_MAX, self._rc_values["yaw"].get() + 25 * yaw_direction))
            )
        else:
            self._rc_values["yaw"].set(RC_CENTER)

        self._rc_values["throttle"].set(
            max(
                RC_MIN,
                min(
                    RC_MAX,
                    self._rc_values["throttle"].get()
                    + 10
                    * (int("w" in self._pressed_keys) - int("s" in self._pressed_keys)),
                ),
            )
        )
        if self._keyboard_enabled.get():
            try:
                self._controller.set_rc_inputs(
                    roll=self._rc_values["roll"].get(),
                    pitch=self._rc_values["pitch"].get(),
                    throttle=self._rc_values["throttle"].get(),
                    yaw=self._rc_values["yaw"].get(),
                )
            except Exception as error:
                self._append_log(f"ERROR: {error}")
                self._keyboard_enabled.set(False)
                self._on_keyboard_control_changed()

        self._root.after(50, self._update_rc_inputs)

    def _connect_vehicle(self) -> None:
        connection_string = self._connection_entry.get().strip()
        if not connection_string:
            return

        self._connection_label.config(text="Connecting...")
        self._connecting = True
        self._append_log("Connecting...")

        self._connect_btn.config(state=tk.DISABLED)
        threading.Thread(
            target=self._connection_worker, args=(connection_string,)
        ).start()
        self._root.after(100, self._check_connection_result)

    def _close_connection(self) -> bool:
        try:
            self._controller.disconnect()
            self._connection_label.config(text="Disconnected")
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
        target_altitude = self._target_altitude_entry.get().strip()
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
                self._connection_label.config(text="Connected")
                self._set_connection_controls(connected=True)
                self._append_log("Connected")

            else:
                self._connection_label.config(text="Connection failed")
                self._set_connection_controls(connected=False)
                self._append_log(f"ERROR: {error}")

        except queue.Empty:
            self._root.after(100, self._check_connection_result)

    def _set_connection_controls(self, *, connected: bool) -> None:
        self._connect_btn.config(state=tk.NORMAL if not connected else tk.DISABLED)
        state = tk.NORMAL if connected else tk.DISABLED
        self._close_connection_btn.config(state=state)
        for btn in self._mode_btn_map.values():
            btn.config(state=state)

    def _append_log(self, message: str) -> None:
        self._logs_area.config(state=tk.NORMAL)
        self._logs_area.insert("end", message + "\n")
        self._logs_area.see("end")
        self._logs_area.config(state=tk.DISABLED)

    def _initialize_root_window(self) -> None:
        self._root.title("Trust Me, It Flies")
        self._root.geometry(f"{ROOT_WINDOW_WIDTH}x{ROOT_WINDOW_HEIGHT}")
        self._root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        self._root.configure(bg=WINDOW_BG)
        self._root.option_add("*Font", ("Arial", 11))

    def _create_section_frame(self, parent: tk.Misc, title: str) -> tk.LabelFrame:
        return tk.LabelFrame(
            parent,
            text=title,
            bg=SECTION_BG,
            fg=MAIN_TEXT_COLOR,
            bd=0,
            padx=10,
            pady=10,
        )

    def _layout_connection_widgets(self) -> None:
        self._connection_frame.pack(fill="x", padx=15, pady=10)
        self._connection_frame.columnconfigure(1, weight=1)

        self._connection_label.grid(row=0, columnspan=2, padx=5, pady=5)
        self._connection_string_label.grid(row=1, column=0, padx=5, pady=5)
        self._connection_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self._connection_buttons_frame.grid(row=2, column=0, columnspan=2, pady=5)
        self._connect_btn.grid(row=0, column=0, padx=5)
        self._close_connection_btn.grid(row=0, column=1, padx=5)

    def _layout_flight_mode_widgets(self) -> None:
        self._flight_mode_frame.pack(fill="x", padx=15, pady=10)

        self._current_mode_label.grid(row=0, columnspan=len(MODE_LIST), padx=5, pady=5)
        for i, btn in enumerate(self._mode_btn_map.values()):
            self._flight_mode_frame.columnconfigure(i, weight=1, uniform="modes")
            btn.grid(row=1, column=i, padx=5, pady=5, sticky="ew")

    def _layout_vehicle_widgets(self) -> None:
        self._vehicle_frame.pack(fill="x", padx=15, pady=10)
        self._vehicle_frame.columnconfigure(0, weight=1)

        self._arm_btn.grid(row=0, column=0, padx=5, pady=5)

        self._takeoff_controls_frame.grid(row=1, column=0, pady=5)
        self._target_altitude_label.grid(row=0, column=0, padx=5)
        self._target_altitude_entry.grid(row=0, column=1, padx=5)
        self._takeoff_btn.grid(row=0, column=2, padx=5)

        self._current_altitude_label.grid(row=2, column=0, pady=5)

    def _layout_logs_widgets(self) -> None:
        self._logs_frame.pack(fill="both", expand=True, padx=15, pady=10)
        self._logs_area.pack(fill="both", expand=True)

    def _layout_rc_controls_widgets(self) -> None:
        self._rc_controls_frame.pack(fill="both", expand=True, padx=15, pady=10)
        self._rc_controls_frame.columnconfigure(0, weight=1)
        self._rc_controls_frame.columnconfigure(1, weight=1)

        self._roll_indicator.grid(row=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self._pitch_indicator.grid(row=1, column=0, padx=10, pady=10, sticky="ns")
        self._throttle_indicator.grid(row=1, column=1, padx=10, pady=10, sticky="ns")
        self._yaw_indicator.grid(row=2, columnspan=2, padx=10, pady=10, sticky="ew")

        self._keyboard_control_btn.grid(row=3, columnspan=2, padx=10, pady=10)
        self._keyboard_control_status_label.grid(row=4, columnspan=2, padx=10, pady=10)

    def _focus_rc_controls(self, event: tk.Event) -> None:
        self._rc_controls_frame.focus_set()

    def _on_key_press(self, event: tk.Event) -> None:
        if (
            isinstance(event.widget, (tk.Entry, tk.Text))
            or not self._keyboard_enabled.get()
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

    def _on_keyboard_control_changed(self) -> None:
        self._pressed_keys.clear()
        enabled = self._keyboard_enabled.get()
        if enabled:
            mode_name = self._controller.mode_name
            if mode_name == "STABILIZE" and self._controller.armed:
                self._keyboard_enabled.set(False)
                self._append_log(
                    "Enable keyboard control before arming in STABILIZE"
                )
                return

            if mode_name == "STABILIZE":
                self._rc_values["throttle"].set(RC_MIN)
            elif mode_name == "LOITER":
                self._rc_values["throttle"].set(
                    RC_CENTER if self._controller.armed else RC_MIN
                )

            self._keyboard_control_status_label.config(text="Keyboard control: ON")
            self._rc_controls_frame.focus_set()

            self._rc_values["roll"].set(RC_CENTER)
            self._rc_values["pitch"].set(RC_CENTER)
            self._rc_values["yaw"].set(RC_CENTER)

        else:
            self._keyboard_control_status_label.config(text="Keyboard control: OFF")
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
            if self._keyboard_enabled.get():
                self._keyboard_enabled.set(False)
                self._on_keyboard_control_changed()


def main() -> None:
    gcs = GroundControlStation()
    gcs.run()


if __name__ == "__main__":
    main()
