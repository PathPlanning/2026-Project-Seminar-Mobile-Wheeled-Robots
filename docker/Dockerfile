# ROS distribution to use
ARG ROS_DISTRO=jazzy

FROM ros:${ROS_DISTRO}-ros-base-noble AS ros2-base

ARG USERNAME=devuser
ARG USER_ID=1000
ARG GROUP_ID=1000
ARG ROS_DISTRO=jazzy

ENV ROS_DISTRO=${ROS_DISTRO}
SHELL ["/bin/bash", "-c"]


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    pkg-config \
    git \
    curl \
    wget \
    ca-certificates \
    nano \
    tmux \
    htop \
    btop \
    tree \
    less \
    unzip \
    python3-pip \
    python3-venv \
    python3-opencv \
    python3-numpy \
    gdb \
    zsh \
    iproute2 \
    iputils-ping \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*


RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-${ROS_DISTRO}-desktop \
    ros-${ROS_DISTRO}-perception \
    ros-dev-tools \
    && rm -rf /var/lib/apt/lists/*

RUN if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then \
    rosdep init; \
fi

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-${ROS_DISTRO}-webots-ros2 \
    ros-${ROS_DISTRO}-ros2-control \
    ros-${ROS_DISTRO}-ros2-controllers \
    ros-${ROS_DISTRO}-xacro \
    ros-${ROS_DISTRO}-joint-state-publisher \
    ros-${ROS_DISTRO}-joint-state-publisher-gui \
    ros-${ROS_DISTRO}-tf2-tools \
    ros-${ROS_DISTRO}-tf-transformations \
    ros-${ROS_DISTRO}-foxglove-bridge \ 
    ros-${ROS_DISTRO}-turtlebot3 \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-${ROS_DISTRO}-robot-localization \
    ros-${ROS_DISTRO}-slam-toolbox \
    ros-${ROS_DISTRO}-navigation2 \
    ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-cartographer \
    ros-${ROS_DISTRO}-cartographer-ros \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp && rm -rf /var/lib/apt/lists/*
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp


RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libegl1 \
    libglx-mesa0 \
    libgl1-mesa-dri \
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*


RUN userdel -r ubuntu; 
RUN groupadd --gid $GROUP_ID $USERNAME \
    && useradd --uid ${USER_ID} --gid ${GROUP_ID} --create-home --shell /bin/zsh ${USERNAME}

RUN echo ${USERNAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USERNAME} \
    && chmod 0440 /etc/sudoers.d/${USERNAME} \
    && chown -R ${USER_ID}:${GROUP_ID} /home/${USERNAME}

USER ${USERNAME}

RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v1.2.1/zsh-in-docker.sh)" -- \
    -p git \
    -p https://github.com/zsh-users/zsh-autosuggestions \
    -p https://github.com/zsh-users/zsh-completions  \
    -p https://github.com/zsh-users/zsh-syntax-highlighting


RUN rosdep update --rosdistro ${ROS_DISTRO}

WORKDIR /home/${USERNAME}
RUN mkdir -p /home/${USERNAME}/examples_ws/
RUN mkdir -p /home/${USERNAME}/practices_ws/
RUN chown ${USERNAME} /home/${USERNAME}/examples_ws/
RUN chown ${USERNAME} /home/${USERNAME}/practices_ws/


WORKDIR /home/${USERNAME}/practices_ws/
COPY --chown=$USERNAME ./practices ./src





WORKDIR /home/${USERNAME}/examples_ws/
COPY --chown=$USERNAME ./examples ./src

RUN sudo apt-get update \
    && source /opt/ros/${ROS_DISTRO}/setup.bash \
    && rosdep install \
        --from-paths src \
        --ignore-src \
        --rosdistro ${ROS_DISTRO} \
        -r \
        -y \
    && colcon build --symlink-install \
    && sudo rm -rf /var/lib/apt/lists/*

RUN echo 'source /opt/ros/${ROS_DISTRO}/setup.zsh' >> ~/.zshrc
RUN echo 'source ~/examples_ws/install/local_setup.zsh' >> ~/.zshrc
RUN echo 'source ~/practices_ws/install/local_setup.zsh' >> ~/.zshrc



RUN echo 'set-option -g default-shell /bin/zsh' >> ~/.tmux.conf
RUN echo 'setw -g mouse on' >> ~/.tmux.conf


WORKDIR /home/${USERNAME}/
