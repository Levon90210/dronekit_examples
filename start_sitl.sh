#!/bin/bash
set -e

show_help() {
    cat <<'HELP'
Usage: start_sitl.sh [--no-gui] [--wipe] [-h|--help]

By default, starts Gazebo and ArduPilot SITL. With DISPLAY set, opens
Gazebo's GUI and MAVProxy's map/console; otherwise runs without windows.

Options:
  --no-gui   Run SITL only using its built-in physics, without Gazebo or windows.
  --wipe     Reset saved autopilot parameters for the selected simulation.
             Without this option, saved parameters are preserved.
  -h, --help Show this help and exit.
HELP
}

RESET_ARGS=()

NO_GUI=0
for arg in "$@"; do
    case "$arg" in
        --no-gui) NO_GUI=1 ;;
        -h|--help) show_help; exit 0 ;;
        --wipe) RESET_ARGS=(-w) ;;
        *) echo "Unknown option: $arg (try --help)" >&2; exit 1 ;;
    esac
done

ARDUPILOT_ROOT="/home/ardupilot/ardupilot"
SIM_VEHICLE="$ARDUPILOT_ROOT/Tools/autotest/sim_vehicle.py"
SITL_STATE_ROOT="/home/ardupilot/sitl-state"
GAZEBO_PARAMS="$ARDUPILOT_ROOT/Tools/autotest/default_params/gazebo-iris.parm"

OUT_PORTS=(--out udp:127.0.0.1:14550 --out udp:127.0.0.1:14450)

if [ "$NO_GUI" -eq 1 ]; then
    /usr/bin/python3 "$SIM_VEHICLE" \
        -v ArduCopter \
        -f quad \
        "${OUT_PORTS[@]}" \
        "${RESET_ARGS[@]}" \
        --no-rebuild \
        --mavproxy-args="--daemon" \
        --use-dir="$SITL_STATE_ROOT/quad"
    exit 0
fi

if [ -n "$DISPLAY" ]; then
    GZ_FLAGS=(-r -v1)
    MAVPROXY_EXTRA="--map --console"
else
    GZ_FLAGS=(-s -r -v1)
    MAVPROXY_EXTRA=""
fi

cleanup() {
    kill "$GZ_PID" 2>/dev/null || true
    wait "$GZ_PID" 2>/dev/null || true
}

gz sim "${GZ_FLAGS[@]}" iris_runway.sdf &
GZ_PID=$!
trap cleanup EXIT

/usr/bin/python3 "$SIM_VEHICLE" \
    -v ArduCopter \
    -f gazebo-iris \
    --model JSON \
    --add-param-file="$GAZEBO_PARAMS" \
    "${OUT_PORTS[@]}" \
    "${RESET_ARGS[@]}" \
    --no-rebuild \
    --mavproxy-args="$MAVPROXY_EXTRA" \
    --use-dir="$SITL_STATE_ROOT/gazebo"
