# GitHub Runner to build container images and update Jupyter Book
FROM quay.io/podman/stable:latest

ARG RUNNER_VERSION="2.317.0"
ARG DEBIAN_FRONTEND=nointeractive
ARG REPO=default
ARG TOKEN=secretinformation

# Provide the Repo and token at run time
ENV TOKEN=${TOKEN} \
    REPO=${REPO}

# Install OS packages required to run the jobs required 
RUN dnf -y update; yum -y install jq \
    git \
    python \
    python-pip \
    svn \
    cpp \
    make \
    autoconf \
    automake \
    patch \
    cmake \
    wget \
    mlocate \
    rpm-build \
    gcc-c++ \
    uuid-devel \
    pkgconfig \
    libtool \
    python-devel \
    openpgm \
    zeromq-devel && \
    dnf -y install 'dnf-command(config-manager)' && \
    dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo && \
    dnf -y install gh

# Install the GitHub runner requirements
RUN cd /home/podman && mkdir actions-runner && cd actions-runner && \
    curl -O -L https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz && \
    tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz && \
    chown -R podman ~podman && /home/podman/actions-runner/bin/installdependencies.sh 

# Set the default working directory to be /home/podman
WORKDIR /home/podman

# Copy the GitHub runner startup script. 
# This script acquires a GitHub runner registration token and requires the repository URL and a User API token
# The two values, REPO & TOKEN, should be provided at container runtime. The API token is sensitive information and should be treated appropriately
COPY start.sh start.sh

# Make the startup script executable
RUN chmod +x start.sh

# Change the default user to be podman
USER podman

# Update PATH to look at the users home directory before looking at the previous PATH values
ENV PATH="/home/podman/.local/bin:$PATH"

# Set the container primary exectuably to run to be the GitHub runner start script
ENTRYPOINT ["./start.sh"]