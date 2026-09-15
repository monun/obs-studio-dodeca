FROM ubuntu:24.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build pkg-config git ca-certificates curl \
    extra-cmake-modules libglib2.0-dev libcurl4-openssl-dev \
    libavcodec-dev libavdevice-dev libavfilter-dev libavformat-dev libavutil-dev \
    libswresample-dev libswscale-dev libjansson-dev libx11-xcb-dev libgles2-mesa-dev \
    libwayland-dev libpipewire-0.3-dev libpulse-dev libx264-dev libmbedtls-dev \
    libgl1-mesa-dev uthash-dev libsimde-dev libluajit-5.1-dev python3-dev \
    libx11-dev libxcb-randr0-dev libxcb-shm0-dev libxcb-xinerama0-dev \
    libxcb-composite0-dev libxinerama-dev libxcb1-dev libxcb-xfixes0-dev \
    swig libxss-dev libglvnd-dev libxkbcommon-dev libasound2-dev libfdk-aac-dev \
    libfontconfig-dev libfreetype6-dev libjack-jackd2-dev libsndio-dev libspeexdsp-dev \
    libudev-dev libv4l-dev libva-dev libvlc-dev libpci-dev libdrm-dev \
    nlohmann-json3-dev libwebsocketpp-dev libasio-dev libqrcodegencpp-dev \
    libffmpeg-nvenc-dev librist-dev libsrt-openssl-dev qt6-base-dev libqt6svg6-dev \
    qt6-base-private-dev libvpl-dev libvpl2 ffmpeg xvfb xauth mesa-utils \
    python3-numpy python3-websocket python3-pyqt6 fonts-noto-cjk xdotool \
    && rm -rf /var/lib/apt/lists/*
