import queue
import threading
import tkinter as tk
from typing import Any, Optional
from dronekit import Vehicle, VehicleMode, connect

ROOT_WINDOW_WIDTH = 400
ROOT_WINDOW_HEIGHT = 300
REQUIRED_ATTRIBUTES = ["gps_0", "armed", "mode", "attitude"]
MODE_LIST = ["GUIDED", "STABILIZE", "LOITER", "LAND", "RTL"]


class GroundControlStation:
    def __init__(self) -> None:
        self._root = tk.Tk()
        self._initialize_root_window()

        self._vehicle: Optional[Vehicle] = None
        self._connecting = False
        self._connection_results: queue.Queue[tuple[bool, Any]] = queue.Queue()

        self._connection_label = tk.Label(self._root, text="Disconnected")
        self._connection_entry = tk.Entry(self._root, width=30)
        self._connect_btn = tk.Button(
            self._root, text="Connect", command=self._connect_vehicle
        )
        self._close_connection_btn = tk.Button(
            self._root,
            text="Close Connection",
            command=self._close_connection,
            state=tk.DISABLED,
        )
        self._mode_btn_map = {
            mode: tk.Button(
                self._root,
                text=mode,
                command=lambda mode=mode: self._set_mode(mode),
                state=tk.DISABLED,
            )
            for mode in MODE_LIST
        }
        self._arm_btn = tk.Button(
            self._root, text="Arm", command=self._arm_vehicle, state=tk.DISABLED
        )
        self._pack_widgets()

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

    def _pack_widgets(self) -> None:
        self._connection_label.pack()
        self._connection_entry.pack()
        self._connect_btn.pack()
        self._close_connection_btn.pack()
        for btn in self._mode_btn_map.values():
            btn.pack()
        self._arm_btn.pack()

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
