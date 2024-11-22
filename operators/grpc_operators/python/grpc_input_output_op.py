#!/usr/bin/env python3

# # SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import logging
from queue import Queue
import cupy as cp
import numpy as np

import holoscan
import holoscan.core
from holoscan.core import Operator, OperatorSpec

import holoscan_pb2


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GrpcInputOp(Operator):
    """Receive a gRPC server message and pass it to a Holoscan pipeline."""
    def __init__(self, fragment, *args, **kwargs):
        self.recv_queue = kwargs.get('queue', None)
        if not self.recv_queue:
            raise ValueError('Receive queue must be provided')
        del kwargs['queue']
        super().__init__(fragment, *args, **kwargs)

    def setup(self, spec: OperatorSpec):
        spec.output("msg_out")

    def message_to_tensor(self, message:holoscan_pb2.EntityRequest) -> holoscan.core.Tensor:
        if len(message.tensors) > 1:
            logger.warning('GrpcInputOp: Received message with more than one tensor, using first tensor')
            
        tensor = message.tensors[0]
        ns = np  # Use NumPy namespace for HOST or SYSTEM memory
        if(tensor.memory_storage_type == holoscan_pb2.Tensor.MemoryStorageType.DEVICE):
            ns = cp  # Use CuPy namespace for DEVICE memory
        DTYPE = ns.uint8
        if tensor.primitive_type == holoscan_pb2.Tensor.PrimitiveType.KUNSIGNED16:
            DTYPE = ns.uint16
        elif tensor.primitive_type == holoscan_pb2.Tensor.PrimitiveType.kFloat32:
            DTYPE = ns.float32

        tensor_buffer = tensor.data
        array_buffer = ns.frombuffer(tensor_buffer, dtype=DTYPE)
        array = array_buffer.reshape(tensor.dimensions)
        return holoscan.as_tensor(array)

    def compute(self, op_input, op_output, context):
        if self.recv_queue.empty():
            logger.debug('GrpcInputOp: No message received, skipping')
            return

        try: 
            message = holoscan_pb2.EntityRequest(self.recv_queue.get())
        except TypeError as e:
            logger.warning('GrpcInputOp: Failed to parse message: %s', e)
            return
        
        tensor = self.message_to_tensor(message)
        op_output.emit({'frame': tensor, 'timestamp': message.timestamp}, "msg_out")


class GrpcOutputOp(Operator):
    """Output a response for the gRPC server to publish"""
    def __init__(self, fragment, *args, **kwargs):
        self.pub_queue = kwargs.get('queue', None)
        if not self.pub_queue:
            raise ValueError('Publish queue must be provided')
        del kwargs['queue']
        super().__init__(fragment, *args, **kwargs)

    def setup(self, spec: OperatorSpec):
        spec.input("msg_in")

    def compute(self, op_input, op_output, context):
        value = op_input.receive("msg_in")
        if not value or type(value) != holoscan_pb2.EntityResponse:
            logger.error('GrpcOutputOp received unexpected message')
            return
        self.pub_queue.put(value)

