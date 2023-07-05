FROM continuumio/miniconda3:4.7.12

# To reduce warnings, see
# https://code.visualstudio.com/docs/remote/containers-advanced
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
COPY ./environment/apt-list.txt /opt/
RUN apt-get update --allow-releaseinfo-change && \
    cat /opt/apt-list.txt | \
    sed 's/#.*$//g' | \
    sed '/^$/d' | \
    tr '\n' ' ' | \
    xargs apt-get install -y

# Python packages
COPY ./environment/dev_requirements.txt /opt/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /opt/dev_requirements.txt
# Hotfix for this bug https://github.com/microsoft/vscode-python/issues/13701
# Jupyter Server does not start in VSCode
# TODO remove this block when resolved
RUN pip install --upgrade pip
RUN pip install 'traitlets==4.3.3' --force-reinstall

# The image above can be stored on the Docker Registry for quicker rebuild.
# See Anian's repo for inspiration.
# Everything below is to create a user with the same credentials as yours.

# Add a non-root user
# These arguments should be passed on build
ARG USERNAME
ARG USER_UID
ARG USER_GID

# Create the user
RUN (groupadd --gid $USER_GID $USERNAME; exit 0) && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    mkdir -p /home/$USERNAME/.vscode-server /home/$USERNAME/.vscode-server-insiders && \
    chown ${USER_UID}:${USER_GID} /home/$USERNAME/.vscode-server*

# Add sudo support to install extra software if needed
RUN apt-get install -y sudo && \
    echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME

# Clean up
RUN apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

# Switch to the user
USER $USERNAME

ENV PATH=$PATH:/workdir

ENV DEBIAN_FRONTEND=dialog \
    IN_DOCKER=true \
    PYTHONPATH=${PYTHONPATH}:/workdir:/workdir/magicstates/Python \
    TROTTER_EMPIRICAL_LAW_FILE=/workdir/alphacore/data/empirical_law.json \
    OVERLAP_EMPIRICAL_LAW_FILE=/workdir/alphacore/data/hfoverlap_empirical_law.json

CMD [ "/bin/bash" ]
