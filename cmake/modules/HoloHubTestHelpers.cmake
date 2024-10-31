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

function(add_engine_generation_test_fixture)
  cmake_parse_arguments(TEST "" "MODEL_FILEPATH;FIXTURE_NAME" "FORWARD_ARGS" ${ARGN})
  string(REGEX MATCH "\\.onnx$" ONNX_EXTENSION ${TEST_MODEL_FILEPATH})
  if(NOT ONNX_EXTENSION)
    message(FATAL_ERROR "Must provide an ONNX model to pre-process for testing")
  endif()
  if(NOT TEST_FORWARD_ARGS)
    set(TEST_FORWARD_ARGS "--fp16")
  endif()

  cmake_path(GET TEST_MODEL_FILEPATH PARENT_PATH MODEL_INPUT_DIR)
  cmake_path(GET TEST_MODEL_FILEPATH STEM MODEL_STEM)
  set(MODEL_OUTPUT_DIR ${MODEL_INPUT_DIR}/engines)
  file(MAKE_DIRECTORY ${MODEL_OUTPUT_DIR})

  set(test_name generate_${MODEL_STEM}_engine)
  if(NOT TEST_FIXTURE_NAME)
    set(TEST_FIXTURE_NAME ${test_name}_fixture)
  endif()
  add_test(
    NAME ${test_name}
    COMMAND python3 ${CMAKE_SOURCE_DIR}/utilities/generate_trt_engine.py
      --input ${TEST_MODEL_FILEPATH}
      --output ${MODEL_OUTPUT_DIR}
      ${TEST_FORWARD_ARGS}
  )
  set_tests_properties(${test_name} PROPERTIES FIXTURES_SETUP ${TEST_FIXTURE_NAME})
endfunction()
