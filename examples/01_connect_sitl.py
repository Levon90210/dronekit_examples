from dronekit import connect

CONNECTION_STRING = "127.0.0.1:14550"
REQUIRED_ATTRIBUTES = ["gps_0", "armed", "mode", "attitude"]

vehicle = connect(
    ip=CONNECTION_STRING,
    wait_ready=REQUIRED_ATTRIBUTES,
)

try:
    print(f"Autopilot firmware version: {vehicle.version}")
    print(f"GPS: {vehicle.gps_0}")
    print(f"Battery: {vehicle.battery}")
    print(f"Last heartbeat: {vehicle.last_heartbeat}")
    print(f"Armable?: {vehicle.is_armable}")
    print(f"System status: {vehicle.system_status.state}")
    print(f"Mode: {vehicle.mode.name}")

finally:
    vehicle.close()
