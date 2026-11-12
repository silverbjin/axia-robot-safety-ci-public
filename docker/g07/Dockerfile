# Public AXIA G07 simulation runtime only. NO instructor/student source,
# private tokens, rosbag evidence or prebuilt ROS workspace.
# Build SHA/digest is recorded by the public CI build workflow.
FROM ros:jazzy-ros-base-noble
LABEL org.opencontainers.image.source="https://github.com/silverbjin/axia-robot-safety-ci-public"
LABEL org.opencontainers.image.description="AXIA G07 ROS 2 Jazzy / Gazebo Harmonic / official Nav2 simulation runtime only"
ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=jazzy \
    ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
COPY docker/g07/osrf-repo-setup.sh /tmp/axia-osrf-setup.sh
RUN bash /tmp/axia-osrf-setup.sh && rm -f /tmp/axia-osrf-setup.sh
COPY docker/g07/runtime-packages.txt /opt/axia/runtime-packages.txt
COPY docker/g07/official-files.sha256 /opt/axia/official-files.sha256
SHELL ["/bin/bash","-o","pipefail","-c"]
RUN set -Eeuo pipefail; \
    mapfile -t pkgs < <(grep -vE '^[[:space:]]*(#|$)' /opt/axia/runtime-packages.txt); \
    [[ "${#pkgs[@]}" == 25 ]]; \
    apt-get update -qq; \
    apt-get install -y -qq --no-install-recommends "${pkgs[@]}" \
      procps git python3-pytest python3-psutil python3-opencv \
      libgl1 libegl1; \
    sha256sum -c /opt/axia/official-files.sha256; \
    python3 -c 'import platform, subprocess, sys; \
assert sys.version_info[:2] == (3,12), sys.version; \
assert platform.machine() == "x86_64"; \
v = subprocess.check_output(["gz","sim","--version"],text=True); \
assert "8.15.0" in v,v; \
print("AXIA_G07_RUNTIME_ONLY_INSTALL_AND_OFFICIAL_SHA256_PASS")'
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /work
