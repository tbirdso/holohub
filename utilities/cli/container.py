#!/usr/bin/env python3
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

import argparse
import os
import subprocess
import sys
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import shutil
import pwd
import grp
from datetime import datetime
import json
import glob
import traceback

from .util import get_host_gpu, get_compute_capacity, get_group_id, run_command, check_nvidia_ctk

class HoloHubContainer:
    """Manages container operations for HoloHub"""
    
    def __init__(self):
        self.script_dir = Path(os.path.dirname(os.path.realpath(__file__)))
        self.holohub_root = self.script_dir
        
        # Environment defaults
        self.holoscan_py_exe = os.environ.get('HOLOSCAN_PY_EXE', 'python3')
        self.holoscan_docker_exe = os.environ.get('HOLOSCAN_DOCKER_EXE', 'docker')
        self.holoscan_sdk_version = 'sdk-latest'
        self.holohub_container_base_name = 'holohub'
        
        self.do_dry_run = False

    def get_default_base_img(self) -> str:
        """Get default base image name"""
        return f"nvcr.io/nvidia/clara-holoscan/holoscan:v3.0.0-{get_host_gpu()}"

    def get_default_img(self) -> str:
        """Get default image name"""
        return f"holohub:ngc-v3.0.0-{get_host_gpu()}"

    def get_ucx_options(self) -> List[str]:
        """Get UCX-related docker options"""
        return [
            '--ipc=host',
            '--cap-add=CAP_SYS_PTRACE',
            '--ulimit=memlock=-1',
            '--ulimit=stack=67108864'
        ]

    def get_conditional_options(self, use_tini: bool = False, persistent: bool = False) -> List[str]:
        """Get conditional docker options"""
        options = []
        
        # Add device mounts
        device_paths = [
            '/usr/lib/libvideomasterhd.so',
            '/opt/deltacast/videomaster/Include',
            '/opt/yuan/qcap/include',
            '/opt/yuan/qcap/lib',
            '/usr/lib/aarch64-linux-gnu/tegra'
        ]
        
        for path in device_paths:
            if os.path.exists(path):
                if os.path.isfile(path):
                    options.append(f'--volume={path}:{path}')
                else:
                    options.append(f'--volume={path}:{path}')

        # Add group permissions
        for group in ['video', 'render', 'docker']:
            gid = get_group_id(group)
            if gid is not None:
                options.append(f'--group-add={gid}')

        # Handle tini and persistence
        if use_tini:
            options.append('--init')
        if not persistent:
            options.append('--rm')

        return options

    def get_dockerfile_path(self, app_name: str = None, language: Optional[str] = 'cpp') -> Path:
        """Get Dockerfile path for an application or default"""
        if not app_name:
            return self.script_dir / "Dockerfile"
            
        app_source = get_app_source_lang_dir(app_name, language, self.script_dir)
        
        # Check metadata.json for dockerfile entry
        try:
            metadata = get_metadata(app_source)
            if "dockerfile" in metadata:
                dockerfile = metadata["dockerfile"].replace("<holohub_app_source>", str(app_source))
                return Path(dockerfile)
        except (FileNotFoundError, KeyError):
            pass
            
        # Check for Dockerfile in application directory
        app_dockerfile = app_source / "Dockerfile"
        if app_dockerfile.exists():
            return app_dockerfile
        
        # Check for Dockerfile in language directory
        lang_dockerfile = app_source / "Dockerfile"
        if lang_dockerfile.exists():
            return lang_dockerfile
            
        # Use default Dockerfile
        return self.script_dir / "Dockerfile"

    def build(self, 
              docker_file: Optional[str] = None,
              base_img: Optional[str] = None,
              img: Optional[str] = None,
              no_cache: bool = False,
              build_args: Optional[str] = None,
              project: Optional[str] = None,
              language: Optional[str] = 'cpp',
              verbose: bool = False) -> None:
        """Build the container image"""
        
        # Get Dockerfile path
        if docker_file:
            docker_file_path = Path(docker_file)
        else:
            docker_file_path = self.get_dockerfile_path(project, language)
            
        base_img = base_img or self.get_default_base_img()
        img = img or self.get_default_img()
        gpu_type = get_host_gpu()
        compute_capacity = get_compute_capacity()

        if verbose:
            print(f"Build (HOLOHUB_ROOT: {self.holohub_root})")
            print(f"Build (gpu_type: {gpu_type})")
            print(f"Build (base_img: {base_img})")
            print(f"Build (docker_file: {docker_file_path})")
            print(f"Build (img: {img})")

        # Check if buildx exists
        try:
            run_command(['docker', 'buildx', 'version'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            fatal("docker buildx plugin is missing. Please install docker-buildx-plugin:\n"
                  "https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository")

        # Set DOCKER_BUILDKIT environment variable
        os.environ['DOCKER_BUILDKIT'] = '1'
        
        cmd = [
            'docker', 'build',
            '--build-arg', f'BUILDKIT_INLINE_CACHE=1',
            '--build-arg', f'BASE_IMAGE={base_img}',
            '--build-arg', f'GPU_TYPE={gpu_type}',
            '--build-arg', f'COMPUTE_CAPACITY={compute_capacity}',
            '--network=host',
        ]
        
        if no_cache:
            cmd.append('--no-cache')
            
        if build_args:
            cmd.extend(build_args.split())
            
        cmd.extend([
            '-f', str(docker_file_path),
            '-t', img,
            str(self.holohub_root)
        ])
        
        run_command(cmd, dry_run=self.do_dry_run)

    def launch(self,
               img: Optional[str] = None,
               local_sdk_root: str = "undefined",
               ssh_x11: bool = False,
               use_tini: bool = False,
               persistent: bool = False,
               nsys_profile: bool = False,
               nsys_location: str = "",
               as_root: bool = False,
               docker_opts: str = "",
               add_volumes: List[str] = None,
               verbose: bool = False,
               dryrun: bool = False,
               extra_args: List[str] = None) -> None:
        """Launch the container"""
        
        check_nvidia_ctk()
        
        img = img or self.get_default_img()
        add_volumes = add_volumes or []
        extra_args = extra_args or []

        # Build docker command
        cmd = [self.holoscan_docker_exe, 'run', '--net', 'host']
        
        # Basic options
        cmd.extend(['--interactive'])
        if sys.stdout.isatty():
            cmd.append('--tty')
            
        # User permissions
        if not as_root:
            cmd.extend(['-u', f'{os.getuid()}:{os.getgid()}'])
        cmd.extend([
            '-v', '/etc/group:/etc/group:ro',
            '-v', '/etc/passwd:/etc/passwd:ro'
        ])
        
        # Workspace mounting
        cmd.extend([
            '-v', f'{self.holohub_root}:/workspace/holohub',
            '-w', '/workspace/holohub'
        ])
        
        # GPU and device access
        cmd.extend([
            '--runtime=nvidia',
            '--gpus', 'all',
            '--cap-add', 'CAP_SYS_PTRACE',
            '--ipc=host',
            '-v', '/dev:/dev',
            '--device-cgroup-rule', 'c 81:* rmw',
            '--device-cgroup-rule', 'c 189:* rmw',
        ])
        
        # Environment variables
        cmd.extend([
            '-e', 'NVIDIA_DRIVER_CAPABILITIES=graphics,video,compute,utility,display',
            '-e', 'HOME=/workspace/holohub'
        ])
        
        # Additional volumes
        for volume in add_volumes:
            base = os.path.basename(volume)
            cmd.extend(['-v', f'{volume}:/workspace/volumes/{base}'])
            
        # Add conditional options
        cmd.extend(self.get_conditional_options(use_tini, persistent))
        
        # Add UCX options
        cmd.extend(self.get_ucx_options())
        
        # Add display server options
        self._add_display_options(cmd, ssh_x11)
        
        # Add local SDK options if provided
        if local_sdk_root != "undefined":
            self._add_local_sdk_options(cmd, local_sdk_root)
            
        # Add docker options if provided
        if docker_opts:
            cmd.extend(docker_opts.split())
            
        # Add the image name
        cmd.append(img)
        
        # Add any extra arguments
        cmd.extend(extra_args)
        
        if verbose:
            print(f"Launch command: {' '.join(cmd)}")
            
        run_command(cmd, dry_run=self.do_dry_run)

    def _add_display_options(self, cmd: List[str], ssh_x11: bool) -> None:
        """Add display-related options to docker command"""
        if 'XDG_SESSION_TYPE' in os.environ:
            cmd.extend(['-e', 'XDG_SESSION_TYPE'])
            if os.environ['XDG_SESSION_TYPE'] == 'wayland':
                cmd.extend(['-e', 'WAYLAND_DISPLAY'])
                
        if 'XDG_RUNTIME_DIR' in os.environ:
            cmd.extend(['-e', 'XDG_RUNTIME_DIR'])
            if os.path.isdir(os.environ['XDG_RUNTIME_DIR']):
                cmd.extend(['-v', f"{os.environ['XDG_RUNTIME_DIR']}:{os.environ['XDG_RUNTIME_DIR']}"])
                
        # Handle X11
        session_type = os.environ.get('XDG_SESSION_TYPE', '')
        if not session_type or session_type in ['x11', 'tty']:
            if 'DISPLAY' in os.environ and shutil.which('xhost'):
                run_command(['xhost', '+local:docker'])
            cmd.extend([
                '-v', '/tmp/.X11-unix:/tmp/.X11-unix',
                '-e', 'DISPLAY'
            ])

    def _add_local_sdk_options(self, cmd: List[str], local_sdk_root: str) -> None:
        """Add Holoscan SDK-related options to docker command"""
        pythonpath = "/workspace/holohub/benchmarks/holoscan_flow_benchmarking"
        
        if os.path.isdir(local_sdk_root):
            cmd.extend(['-v', f'{local_sdk_root}:/workspace/holoscan-sdk'])
            cmd.extend([
                '-e', 'HOLOSCAN_LIB_PATH=/workspace/holoscan-sdk/build/lib',
                '-e', 'HOLOSCAN_SAMPLE_DATA_PATH=/workspace/holoscan-sdk/data',
                '-e', 'HOLOSCAN_TESTS_DATA_PATH=/workspace/holoscan-sdk/tests/data'
            ])
            pythonpath = f"/workspace/holoscan-sdk/build/python/lib:{pythonpath}"
        else:
            pythonpath = f"/opt/nvidia/holoscan/python/lib:{pythonpath}"
            
        cmd.extend(['-e', f'PYTHONPATH={pythonpath}'])