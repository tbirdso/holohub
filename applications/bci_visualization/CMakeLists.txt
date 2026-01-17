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
  # Expected sample was collected with Flow 2, exclude Flow >=2.1 data as unused
  add_custom_target(bci_visualization_data ALL
    COMMAND hf download KernelCo/holohub_bci_visualization
            --repo-type dataset
            --local-dir "${BCI_DATA_DIR}"
            --exclude "flow_2_1/*"
            --exclude "flow_2_2/*"
            --exclude "flow_2_3/*"
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

# Add testing
if(BUILD_TESTING)

  set(RECORDING_DIR ${CMAKE_CURRENT_BINARY_DIR}/recording_output)
  set(SOURCE_VIDEO_BASENAME python_bci_visualization_output)
  set(VALIDATION_FRAMES_DIR ${CMAKE_SOURCE_DIR}/applications/bci_visualization/testing/)

  file(MAKE_DIRECTORY ${RECORDING_DIR})

  # Patch the application to enable recording for testing
  add_custom_command(OUTPUT bci_visualization_test.py
    COMMAND patch -u -o bci_visualization_test.py ${CMAKE_CURRENT_SOURCE_DIR}/bci_visualization.py
        ${CMAKE_SOURCE_DIR}/applications/bci_visualization/testing/bci_visualization.patch
    COMMAND sed -i "s#RECORDING_DIR#${RECORDING_DIR}#g" bci_visualization_test.py
    COMMAND sed -i "s#SOURCE_VIDEO_BASENAME#${SOURCE_VIDEO_BASENAME}#g" bci_visualization_test.py
  )

  add_custom_target(bci_visualization_test ALL
    DEPENDS "bci_visualization_test.py"
  )

  add_dependencies(bci_visualization_test python_bci_visualization)

  # Integration test: runs the application end-to-end
  add_test(NAME bci_visualization_python_test
    COMMAND python3 ${CMAKE_CURRENT_BINARY_DIR}/bci_visualization_test.py
            --renderer_config ${CMAKE_CURRENT_BINARY_DIR}/config.json
            --record_output
            --recording_dir ${RECORDING_DIR}
            --mask_path ${HOLOHUB_DATA_DIR}/${PROJECT_NAME}/bci_visualization/anatomy_labels_high_res.nii.gz
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
  )

  set_property(TEST bci_visualization_python_test PROPERTY ENVIRONMENT
               "PYTHONPATH=${GXF_LIB_DIR}/../python/lib:${CMAKE_BINARY_DIR}/python/lib"
               "HOLOSCAN_INPUT_PATH=${HOLOHUB_DATA_DIR}/bci_visualization")

  set_tests_properties(bci_visualization_python_test PROPERTIES
    DEPENDS bci_visualization_test
    PASS_REGULAR_EXPRESSION "App has finished running."
    FAIL_REGULAR_EXPRESSION "[^a-z]Error;ERROR;Failed"
  )

  # Render validation test: validates at least 10 frames match expectations
  add_test(NAME bci_visualization_python_render_test
    COMMAND python3 ${CMAKE_SOURCE_DIR}/utilities/video_validation.py
    --source_video_dir ${RECORDING_DIR}
    --source_video_basename ${SOURCE_VIDEO_BASENAME}
    --output_dir ${RECORDING_DIR}
    --validation_frames_dir ${VALIDATION_FRAMES_DIR}
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
  )

  set_tests_properties(bci_visualization_python_render_test PROPERTIES
    DEPENDS bci_visualization_python_test
    PASS_REGULAR_EXPRESSION "Valid video output!"
  )

endif()
