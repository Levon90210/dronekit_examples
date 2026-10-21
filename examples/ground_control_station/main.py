import queue
import threading
import tkinter as tk
from typing import Any, Optional
from dronekit import Vehicle, VehicleMode, connect

ROOT_WINDOW_WIDTH = 400
ROOT_WINDOW_HEIGHT = 300
REQUIRED_ATTRIBUTES = ["gps_0", "armed", "mode", "attitude"]
MODE_LIST = ["GUIDED", "STABILIZE", "LOITER", "LAND", "RTL"]


def main() -> None:
    def connection_worker(connection_string: str) -> None:
        try:
            vehicle = connect(connection_string, wait_ready=REQUIRED_ATTRIBUTES)
            connection_results.put((True, vehicle))

        except Exception as error:
            connection_results.put((False, error))

    def connect_vehicle() -> None:
        nonlocal connecting

        connection_string = input_field.get().strip()
        if not connection_string:
            return

        connection_label.config(text="Connecting...")
        connecting = True

        connect_btn.config(state=tk.DISABLED)
        threading.Thread(target=connection_worker, args=(connection_string,)).start()
        root.after(100, check_connection_result)

    def check_connection_result() -> None:
        nonlocal vehicle, connecting
        try:
            success, vehicle_or_error = connection_results.get_nowait()
            connecting = False

            if success:
                vehicle = vehicle_or_error
                connection_label.config(text="Connected")

                close_connection_btn.config(state=tk.NORMAL)
                for btn in mode_btn_map.values():
                    btn.config(state=tk.NORMAL)
                arm_btn.config(state=tk.NORMAL)

            else:
                print(vehicle_or_error)
                connection_label.config(text="Connection failed")

                connect_btn.config(state=tk.NORMAL)

        except queue.Empty:
            root.after(100, check_connection_result)

    def close_connection() -> None:
        nonlocal vehicle
        if vehicle is not None:
            vehicle.close()
            vehicle = None

        connection_label.config(text="Disconnected")

        connect_btn.config(state=tk.NORMAL)
        close_connection_btn.config(state=tk.DISABLED)
        for btn in mode_btn_map.values():
            btn.config(state=tk.DISABLED)
        arm_btn.config(state=tk.DISABLED)

    def set_mode(mode_name: str) -> None:
        if vehicle is not None:
            vehicle.mode = VehicleMode(name=mode_name)

    def arm_vehicle() -> None:
        if vehicle is not None:
            if vehicle.is_armable:
                vehicle.armed = True

            else:
                print("Vehicle is not armable")

    def on_window_close() -> None:
        if connecting:
            print("Wait for the connection attempt to finish")
        else:
            close_connection()
            root.destroy()

    root = tk.Tk()

    root.title("Ground Control Station")
    root.geometry(f"{ROOT_WINDOW_WIDTH}x{ROOT_WINDOW_HEIGHT}")
    root.protocol("WM_DELETE_WINDOW", on_window_close)

    connection_label = tk.Label(root, text="Disconnected")
    connection_label.pack()

    vehicle: Optional[Vehicle] = None
    connecting = False
    connection_results: queue.Queue[tuple[bool, Any]] = queue.Queue()

    input_field = tk.Entry(root, width=30)
    input_field.pack()

    connect_btn = tk.Button(root, text="Connect", command=connect_vehicle)
    connect_btn.pack()

    close_connection_btn = tk.Button(
        root, text="Close Connection", command=close_connection, state=tk.DISABLED
    )
    close_connection_btn.pack()

    mode_btn_map = {
        mode: tk.Button(
            root, text=mode, command=lambda mode=mode: set_mode(mode), state=tk.DISABLED
        )
        for mode in MODE_LIST
    }
    for btn in mode_btn_map.values():
        btn.pack()

    arm_btn = tk.Button(root, text="Arm", command=arm_vehicle, state=tk.DISABLED)
    arm_btn.pack()

    root.mainloop()


if __name__ == "__main__":
    main()
