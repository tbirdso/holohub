#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

# Add Holoscan SDK components for C++ and Python development to a pre-existing CUDA development container.
# Assumes that:
# - The CUDA development container has appropriate CUDA APT repositories enabled
# - The CUDA development container has the CUDA Toolkit installed
set -ex

CUDA_MAJOR_VERSION=$(nvcc --version | grep -oE 'release [0-9]+' | cut -d' ' -f2)

# Install latest Holoscan SDK Debian and Python components
apt update
HOLOSCAN_PKGS=$(apt-cache search holoscan)
HOLOSCAN_PKG=$(echo "$HOLOSCAN_PKGS" | grep "cuda-${CUDA_MAJOR_VERSION}" | awk '{print $1}' | head -n1)
if [ -z "$HOLOSCAN_PKG" ]; then
    echo "No holoscan package found for CUDA version $CUDA_MAJOR_VERSION"
    exit 1
fi
apt install -y --no-install-recommends "$HOLOSCAN_PKG"

# Install latest Holoscan SDK Python components
pip install holoscan-cu${CUDA_MAJOR_VERSION} cupy-cuda${CUDA_MAJOR_VERSION}x
python3 -c "pass"  # dummy command to run wheel-axle-runtime post-installation setup
