# syntax=docker/dockerfile:1

# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ARG BASE_IMAGE
ARG GPU_TYPE
ARG COMPUTE_CAPACITY
############################################################
# Torch image (Used to extract the ARM64 dGPU pytorch wheel)
############################################################
FROM nvcr.io/nvidia/pytorch:23.10-py3 as pytorch

############################################################
# Base image
############################################################
FROM ${BASE_IMAGE} as base
ARG DEBIAN_FRONTEND=noninteractive

# Holohub setup
RUN mkdir -p /tmp/scripts
COPY run /tmp/scripts/
RUN chmod +x /tmp/scripts/run
RUN /tmp/scripts/run setup

# Copy over app-specific requirements
COPY applications/florence-2-vision/requirements.txt /tmp/requirements.txt

# Install setuptools prior to all other requirements to avoid install errors
RUN python3 -m pip install --no-cache-dir setuptools && \
    python3 -m pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the Torch wheel from the PyTorch image. This is necessary because the PyTorch wheel is not available for ARM64 on PyPI.
WORKDIR /tmp/pip/
COPY --from=pytorch /tmp/pip/torch*.whl /tmp/pip/

# Install the Torch wheel based on the target architecture
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "amd64" ]; then \
        echo "Building for x86 (AMD64) architecture"; \
        python3 -m pip install torch==2.1.0; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
        echo "Building for ARM64 architecture"; \
        python3 -m pip install /tmp/pip/torch-2.1.0a0+32f93b1-cp310-cp310-linux_aarch64.whl; \
    else \
        echo "Unknown architecture: $TARGETARCH"; \
        exit 1; \
    fi

# Download the Florence-2 model
RUN huggingface-cli download microsoft/Florence-2-large-ft \
    --local-dir /workspace/volumes/models/microsoft/Florence-2-large-ft --cache-dir /workspace/volumes/models/microsoft/Florence-2-large-ft

# Build/install flash-attention 2 (NOTE: on Arm64 this will take between 1-1.5 hours)
# MAX_JOBS is set to 4 to avoid running out of memory
RUN MAX_JOBS=4 python3 -m pip install --no-cache-dir --no-build-isolation flash-attn

# Install QT dependencies
RUN apt-get install -y \
    qt6-base-dev \
    libxcb-cursor0

WORKDIR /workspace/holohub
