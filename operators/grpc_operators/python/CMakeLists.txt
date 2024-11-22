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

find_package(Python3 COMPONENTS Interpreter REQUIRED)

execute_process(
    COMMAND ${Python3_EXECUTABLE} -m grpc_tools.protoc --version
    RESULT_VARIABLE _grpc_tools_protoc_result
    OUTPUT_VARIABLE _grpc_tools_protoc_out
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
if(NOT _grpc_tools_protoc_result EQUAL 0)
    message(FATAL_ERROR "grpc_tools.protoc not found")
endif()


add_custom_command(
    OUTPUT
        ${CMAKE_CURRENT_BINARY_DIR}/holoscan_pb2.py
        ${CMAKE_CURRENT_BINARY_DIR}/holoscan_pb2_grpc.py
        ${CMAKE_CURRENT_BINARY_DIR}/holoscan_pb2.pyi
    DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/../protos/holoscan.proto
    COMMAND
    python3 -m grpc_tools.protoc
        -I ${CMAKE_CURRENT_SOURCE_DIR}/protos
        --python_out=${CMAKE_CURRENT_BINARY_DIR}
        --pyi_out=${CMAKE_CURRENT_BINARY_DIR}
        --grpc_python_out=${CMAKE_CURRENT_BINARY_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/protos/camera_stream.proto
)

set(HOLOSCAN_GRPC_PY_FILES
    __init__.py
    grpc_input_output_op.py
)
foreach(_file ${HOLOSCAN_GRPC_PY_FILES})
    add_custom_command(
        OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/${_file}
        DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${_file}
        COMMAND
        ${CMAKE_COMMAND} -E copy_if_different
            ${CMAKE_CURRENT_SOURCE_DIR}/${_file}
            ${CMAKE_CURRENT_BINARY_DIR}/${_file}
    )
endforeach()

add_custom_target(
    holoscan_grpc_py ALL
    DEPENDS
        ${CMAKE_CURRENT_BINARY_DIR}/__init__.py
        ${CMAKE_CURRENT_BINARY_DIR}/grpc_input_output_op.py
        ${CMAKE_CURRENT_BINARY_DIR}/camera_stream_pb2.py
        ${CMAKE_CURRENT_BINARY_DIR}/camera_stream_pb2_grpc.py
        ${CMAKE_CURRENT_BINARY_DIR}/camera_stream_pb2.pyi
)
