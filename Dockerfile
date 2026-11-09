FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC

# --- base deps + Gazebo Harmonic apt repo ---
RUN apt-get update && apt-get install -y --no-install-recommends \
        sudo git wget curl lsb-release gnupg build-essential cmake vim \
        software-properties-common ca-certificates tzdata \
    && wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
        > /etc/apt/sources.list.d/gazebo-stable.list \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
        gz-harmonic libgz-sim8-dev rapidjson-dev libopencv-dev \
        libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
        libgl1-mesa-dri libglx-mesa0 mesa-utils x11-apps \
        python3.9 python3.9-venv python3.9-dev python3.9-tk \
    && rm -rf /var/lib/apt/lists/*

# ArduPilot's build scripts refuse to run as root
RUN useradd -m -s /bin/bash ardupilot \
    && echo "ardupilot ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ardupilot
USER ardupilot
ENV USER=ardupilot
WORKDIR /home/ardupilot

# --- ArduPilot SITL ---
RUN git clone --recurse-submodules -j8 https://github.com/ArduPilot/ardupilot.git
# Tested source revision; override the build argument for deliberate upgrades.
ARG ARDUPILOT_REV=b7c08d4dbc69f58f5636642698b63a9130725db6
RUN git -C ardupilot fetch origin "$ARDUPILOT_REV" \
    && git -C ardupilot checkout --detach FETCH_HEAD \
    && git -C ardupilot submodule update --init --recursive -j 8
RUN cd ardupilot && Tools/environment_install/install-prereqs-ubuntu.sh -y
ENV PATH="/home/ardupilot/.local/bin:/home/ardupilot/ardupilot/Tools/autotest:${PATH}"
RUN cd ardupilot && ./waf configure --board sitl && ./waf copter

# --- ardupilot_gazebo plugin (Gazebo Harmonic) ---
ARG ARDUPILOT_GAZEBO_REV=f116b03552d05c8d0b0bed5ed67033a1183121d1
RUN git clone --no-checkout https://github.com/ArduPilot/ardupilot_gazebo.git \
    && git -C ardupilot_gazebo checkout --detach "$ARDUPILOT_GAZEBO_REV" \
    && cd ardupilot_gazebo && mkdir build && cd build \
    && cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo && make -j$(nproc)
ENV GZ_SIM_SYSTEM_PLUGIN_PATH=/home/ardupilot/ardupilot_gazebo/build \
    GZ_SIM_RESOURCE_PATH=/home/ardupilot/ardupilot_gazebo/models:/home/ardupilot/ardupilot_gazebo/worlds

# Python 3.9 environment for the DroneKit GCS; simulator tools use system Python.
COPY --chown=ardupilot:ardupilot requirements-gcs.txt /home/ardupilot/requirements-gcs.txt
RUN python3.9 -m venv /home/ardupilot/venv \
    && /home/ardupilot/venv/bin/python -m pip install --no-cache-dir --no-deps \
        pip==26.0.1 setuptools==79.0.1 wheel==0.48.0 packaging==26.3 \
    && /home/ardupilot/venv/bin/python -m pip install --no-cache-dir \
        --no-deps --no-build-isolation -r /home/ardupilot/requirements-gcs.txt \
    && /home/ardupilot/venv/bin/python -m pip check

RUN /home/ardupilot/venv/bin/python -c 'import dronekit, tkinter, tkintermapview'

COPY --chown=ardupilot:ardupilot entrypoint.sh start_sitl.sh /home/ardupilot/
RUN chmod +x /home/ardupilot/entrypoint.sh /home/ardupilot/start_sitl.sh \
    && mkdir /home/ardupilot/dronekit_examples \
    && mkdir /home/ardupilot/sitl-state

WORKDIR /home/ardupilot/dronekit_examples
ENTRYPOINT ["/home/ardupilot/entrypoint.sh"]
CMD ["bash"]
