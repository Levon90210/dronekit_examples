#!/bin/bash
set -e

# with a working $DISPLAY (X server on the host), run Gazebo's GUI client too and
# add MAVProxy's map window; otherwise stay headless (server-only, no map)
if [ -n "$DISPLAY" ]; then
    GZ_FLAGS="-r -v1"
    MAVPROXY_EXTRA="--daemon --map --console"
else
    GZ_FLAGS="-s -r -v1"
    MAVPROXY_EXTRA="--daemon"
fi

gz sim $GZ_FLAGS iris_runway.sdf &
GZ_PID=$!
trap 'kill $GZ_PID 2>/dev/null' EXIT

# ArduPilot SITL + its own MAVProxy, extra output on :14450 for the dronekit examples.
# Runs in the foreground - Ctrl-C stops the whole stack. Run this in one terminal,
# then `docker exec -it <container> bash` in a second terminal to run the examples.
cd /home/ardupilot/ardupilot/ArduCopter
sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON \
    --add-param-file=/home/ardupilot/ardupilot/Tools/autotest/default_params/gazebo-iris.parm \
    --out udp:127.0.0.1:14550 \
    --no-rebuild -w --mavproxy-args="$MAVPROXY_EXTRA"
