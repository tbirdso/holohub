#!/bin/bash
# SPDX-FileCopyrightText: Copyright (c) 2025-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

# Script to generate reference frames for the BCI Visualization integration test.
# This script runs the application, records the output, converts to PNG, and
# copies the first 10 frames as reference images.
#
# Usage:
#   ./generate_reference_frames.sh [BUILD_DIR] [DATA_DIR]
#
# Arguments:
#   BUILD_DIR - Path to the holohub build directory (default: ../../../build)
#   DATA_DIR  - Path to the bci_visualization data (default: ../../../data/bci_visualization)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
HOLOHUB_DIR="$(dirname "$(dirname "$APP_DIR")")"

BUILD_DIR="${1:-${HOLOHUB_DIR}/build/bci_visualization}"
DATA_DIR="${2:-${HOLOHUB_DIR}/data/bci_visualization}"

RECORDING_DIR="${BUILD_DIR}/applications/bci_visualization/recording_output"
SOURCE_VIDEO_BASENAME="python_bci_visualization_output"

echo "=============================================="
echo "BCI Visualization Reference Frame Generator"
echo "=============================================="
echo "Script directory: ${SCRIPT_DIR}"
echo "Application directory: ${APP_DIR}"
echo "Holohub directory: ${HOLOHUB_DIR}"
echo "Build directory: ${BUILD_DIR}"
echo "Data directory: ${DATA_DIR}"
echo "Recording directory: ${RECORDING_DIR}"
echo "=============================================="

# Check if data directory exists
if [ ! -d "${DATA_DIR}" ]; then
    echo "ERROR: Data directory not found: ${DATA_DIR}"
    echo ""
    echo "Please download the BCI visualization data first:"
    echo "  hf download KernelCo/holohub_bci_visualization --repo-type dataset --local-dir ${DATA_DIR}"
    exit 1
fi

# Check if build directory exists
if [ ! -d "${BUILD_DIR}" ]; then
    echo "ERROR: Build directory not found: ${BUILD_DIR}"
    echo ""
    echo "Please build the application first:"
    echo "  ./run build bci_visualization --configure-args \"-DBUILD_TESTING=ON\""
    exit 1
fi

# Check if the test script exists
TEST_SCRIPT="${BUILD_DIR}/applications/bci_visualization/bci_visualization_test.py"
if [ ! -f "${TEST_SCRIPT}" ]; then
    echo "ERROR: Test script not found: ${TEST_SCRIPT}"
    echo ""
    echo "Please build the application with testing enabled:"
    echo "  ./run build bci_visualization --configure-args \"-DBUILD_TESTING=ON\""
    exit 1
fi

# Create recording directory
mkdir -p "${RECORDING_DIR}"

echo ""
echo "Step 1: Running application with recording enabled..."
echo "----------------------------------------------"

cd "${BUILD_DIR}/applications/bci_visualization"
ctest -C Release -R bci_visualization_python_test -V

echo ""
echo "Step 2: Converting recorded GXF entities to PNG images..."
echo "----------------------------------------------"

python3 "${HOLOHUB_DIR}/utilities/convert_gxf_entities_to_images.py" \
    --directory "${RECORDING_DIR}" \
    --basename "${SOURCE_VIDEO_BASENAME}" \
    --outputdir "${RECORDING_DIR}" \
    --outputname "source"

echo ""
echo "Step 3: Copying first 10 frames as reference images..."
echo "----------------------------------------------"

for i in $(seq 1 10); do
    PADDED=$(printf "%04d" $i)
    SRC="${RECORDING_DIR}/source${PADDED}.png"
    DST="${SCRIPT_DIR}/${PADDED}.png"
    
    if [ -f "${SRC}" ]; then
        cp "${SRC}" "${DST}"
        echo "  Copied ${PADDED}.png"
    else
        echo "  WARNING: Source frame not found: ${SRC}"
    fi
done

echo ""
echo "=============================================="
echo "Reference frame generation complete!"
echo "=============================================="
echo ""
echo "Generated reference frames in: ${SCRIPT_DIR}"
ls -la "${SCRIPT_DIR}"/*.png 2>/dev/null || echo "  No PNG files found"
echo ""
echo "You can now run the integration tests:"
echo "  cd ${BUILD_DIR} && ctest -R bci_visualization -V"
