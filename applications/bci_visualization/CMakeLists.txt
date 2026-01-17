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

cmake_minimum_required(VERSION 3.20)
project(bci_visualization LANGUAGES NONE)

find_package(holoscan 2.0 REQUIRED CONFIG
             PATHS "/opt/nvidia/holoscan" "/workspace/holoscan-sdk/install")

# Default to download datasets
option(HOLOHUB_DOWNLOAD_DATASETS "Download datasets" ON)

# Download the BCI visualization data from Hugging Face
if(HOLOHUB_DOWNLOAD_DATASETS)
  set(BCI_DATA_DIR "${HOLOHUB_DATA_DIR}/bci_visualization")

  # Custom target with USES_TERMINAL to show real-time download progress
  # The hf CLI is idempotent - it verifies file hashes and skips existing files
  add_custom_target(bci_visualization_data ALL
    COMMAND hf download KernelCo/holohub_bci_visualization
            --repo-type dataset
            --local-dir "${BCI_DATA_DIR}"
    COMMENT "Downloading BCI visualization dataset from Hugging Face"
    USES_TERMINAL
  )
endif()

add_subdirectory(operators)

# Copy application files to binary directory
add_custom_target(python_bci_visualization ALL
  COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_CURRENT_SOURCE_DIR}/bci_visualization.py" ${CMAKE_CURRENT_BINARY_DIR}
  COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_CURRENT_SOURCE_DIR}/bci_visualization.yaml" ${CMAKE_CURRENT_BINARY_DIR}
  COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_CURRENT_SOURCE_DIR}/config.json" ${CMAKE_CURRENT_BINARY_DIR}
  COMMAND ${CMAKE_COMMAND} -E copy_directory "${CMAKE_CURRENT_SOURCE_DIR}/operators" ${CMAKE_CURRENT_BINARY_DIR}/operators
  COMMAND ${CMAKE_COMMAND} -E copy_directory "${CMAKE_CURRENT_SOURCE_DIR}/streams" ${CMAKE_CURRENT_BINARY_DIR}/streams
  COMMAND ${CMAKE_COMMAND} -E copy_directory "${CMAKE_CURRENT_SOURCE_DIR}/utils" ${CMAKE_CURRENT_BINARY_DIR}/utils
  DEPENDS
    "bci_visualization.py"
    "bci_visualization.yaml"
    "config.json"
  BYPRODUCTS
    "bci_visualization.py"
    "bci_visualization.yaml"
    "config.json"
)

# Add data download dependency (data downloads before app files are copied)
if(HOLOHUB_DOWNLOAD_DATASETS)
  add_dependencies(python_bci_visualization bci_visualization_data)
endif()
