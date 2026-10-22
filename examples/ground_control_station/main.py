import queue
import threading
import tkinter as tk
from typing import Any, Optional
from dronekit import Vehicle, VehicleMode, connect

from constants import *


class GroundControlStation:
    def __init__(self) -> None:
        self._root = tk.Tk()
        self._initialize_root_window()

        self._vehicle: Optional[Vehicle] = None
        self._connecting = False
        self._connection_results: queue.Queue[tuple[bool, Any]] = queue.Queue()

        self._connection_frame = tk.LabelFrame(
            self._root,
            text="Connection",
            bg=SECTION_BG,
            fg=MAIN_TEXT_COLOR,
            bd=0,
            padx=10,
            pady=10,
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
        self._connect_btn = tk.Button(
            self._connection_frame,
            text="Connect",
            command=self._connect_vehicle,
            bg=PRIMARY_BG,
            fg=MAIN_TEXT_COLOR,
            activebackground=PRIMARY_ACTIVE_BG,
            activeforeground=MAIN_TEXT_COLOR,
            disabledforeground=SECONDARY_TEXT_COLOR,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=7,
        )
        self._close_connection_btn = tk.Button(
            self._connection_frame,
            text="Close Connection",
            command=self._close_connection,
            state=tk.DISABLED,
            bg=SECONDARY_BG,
            fg=MAIN_TEXT_COLOR,
            activebackground=SECONDARY_ACTIVE_BG,
            activeforeground=MAIN_TEXT_COLOR,
            disabledforeground=SECONDARY_TEXT_COLOR,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=7,
        )
        self._layout_connection_widgets()

        self._flight_mode_frame = tk.LabelFrame(
            self._root,
            text="Flight modes",
            bg=SECTION_BG,
            fg=MAIN_TEXT_COLOR,
            bd=0,
            padx=10,
            pady=10,
        )
        self._mode_btn_map = {
            mode: tk.Button(
                self._flight_mode_frame,
                text=mode,
                command=lambda mode=mode: self._set_mode(mode),
                state=tk.DISABLED,
                bg=SECONDARY_BG,
                fg=MAIN_TEXT_COLOR,
                activebackground=SECONDARY_ACTIVE_BG,
                activeforeground=MAIN_TEXT_COLOR,
                disabledforeground=SECONDARY_TEXT_COLOR,
                relief=tk.FLAT,
                bd=0,
                padx=12,
                pady=7,
            )
            for mode in MODE_LIST
        }
        self._layout_flight_mode_widgets()

        self._vehicle_frame = tk.LabelFrame(
            self._root,
            text="Vehicle",
            bg=SECTION_BG,
            fg=MAIN_TEXT_COLOR,
            bd=0,
            padx=10,
            pady=10,
        )
        self._arm_btn = tk.Button(
            self._vehicle_frame,
            text="Arm",
            command=self._arm_vehicle,
            state=tk.DISABLED,
            bg=ARM_BG,
            fg=INPUT_BG,
            activebackground=ARM_ACTIVE_BG,
            activeforeground=INPUT_BG,
            disabledforeground=INPUT_BG,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=7,
        )
        self._layout_vehicle_widgets()

    def run(self) -> None:
        self._root.mainloop()

    def _connect_vehicle(self) -> None:
        connection_string = self._connection_entry.get().strip()
        if not connection_string:
            return

        self._connection_label.config(text="Connecting...")
        self._connecting = True

        self._connect_btn.config(state=tk.DISABLED)
        threading.Thread(
            target=self._connection_worker, args=(connection_string,)
        ).start()
        self._root.after(100, self._check_connection_result)

    def _close_connection(self) -> None:
        if self._vehicle is not None:
            self._vehicle.close()
            self._vehicle = None

        self._connection_label.config(text="Disconnected")
        self._set_connection_controls(connected=False)

    def _set_mode(self, mode_name: str) -> None:
        if self._vehicle is not None:
            self._vehicle.mode = VehicleMode(name=mode_name)

    def _arm_vehicle(self) -> None:
        if self._vehicle is not None:
            if self._vehicle.is_armable:
                self._vehicle.armed = True

            else:
                print("Vehicle is not armable")

    def _connection_worker(self, connection_string: str) -> None:
        try:
            vehicle = connect(connection_string, wait_ready=REQUIRED_ATTRIBUTES)
            self._connection_results.put((True, vehicle))

        except Exception as error:
            self._connection_results.put((False, error))

    def _check_connection_result(self) -> None:
        try:
            success, vehicle_or_error = self._connection_results.get_nowait()
            self._connecting = False

            if success:
                self._vehicle = vehicle_or_error
                self._connection_label.config(text="Connected")
                self._set_connection_controls(connected=True)

            else:
                print(vehicle_or_error)
                self._connection_label.config(text="Connection failed")
                self._set_connection_controls(connected=False)

        except queue.Empty:
            self._root.after(100, self._check_connection_result)

    def _set_connection_controls(self, *, connected: bool) -> None:
        self._connect_btn.config(state=tk.NORMAL if not connected else tk.DISABLED)
        state = tk.NORMAL if connected else tk.DISABLED
        self._close_connection_btn.config(state=state)
        for btn in self._mode_btn_map.values():
            btn.config(state=state)
        self._arm_btn.config(state=state)

    def _initialize_root_window(self) -> None:
        self._root.title("Ground Control Station")
        self._root.geometry(f"{ROOT_WINDOW_WIDTH}x{ROOT_WINDOW_HEIGHT}")
        self._root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        self._root.configure(bg=WINDOW_BG)
        self._root.option_add("*Font", ("Arial", 11))

    def _layout_connection_widgets(self) -> None:
        self._connection_frame.pack(fill="x", padx=15, pady=10)
        self._connection_frame.columnconfigure(1, weight=1)
        self._connection_label.grid(row=0, columnspan=2, padx=5, pady=5)
        self._connection_string_label.grid(row=1, column=0, padx=5, pady=5)
        self._connection_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self._connect_btn.grid(row=2, column=0, padx=5, pady=5)
        self._close_connection_btn.grid(row=2, column=1, padx=5, pady=5)

    def _layout_flight_mode_widgets(self) -> None:
        self._flight_mode_frame.pack(fill="x", padx=15, pady=10)
        for i, btn in enumerate(self._mode_btn_map.values()):
            self._flight_mode_frame.columnconfigure(i, weight=1, uniform="modes")
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")

    def _layout_vehicle_widgets(self) -> None:
        self._vehicle_frame.pack(fill="x", padx=15, pady=10)
        self._vehicle_frame.columnconfigure(0, weight=1)
        self._arm_btn.grid(row=0, column=0, padx=5, pady=5)

    def _on_window_close(self) -> None:
        if self._connecting:
            print("Wait for the connection attempt to finish")
        else:
            self._close_connection()
            self._root.destroy()


def main() -> None:
    gcs = GroundControlStation()
    gcs.run()


if __name__ == "__main__":
    main()
