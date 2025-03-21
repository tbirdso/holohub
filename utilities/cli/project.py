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
from enum import Enum

from .util import fatal

from dataclasses import dataclass
from typing import List, Optional

class ProjectType(Enum):
    APP = "app"
    BENCHMARK = "benchmark"
    GXF_EXTENSION = "gxf_extension"
    OPERATOR = "operator"
    PKG = "pkg"
    WORKFLOW = "workflow"


@dataclass
class Author:
    name: str
    affiliation: str

@dataclass
class VersionedDependency:
    name: str
    version: str

@dataclass
class HardwareDescriptor:
    name: str
    description: str
    version: Optional[str] = None
    required: bool = True

@dataclass
class SdkVersion:
    minimum_required_version: str
    tested_versions: List[str]

@dataclass
class Dependencies:
    data: Optional[List[str]] = None
    gxf_extensions: Optional[List[VersionedDependency]] = None
    hardware: Optional[List[HardwareDescriptor]] = None

@dataclass
class RunCommand:
    command: str
    workdir: Optional[str] = None

@dataclass
class ProjectMetadata:
    metadata_filepath: Path
    project_type: ProjectType
    name: str
    description: str
    authors: List[Author]
    version: str
    platforms: List[str]
    sdk_version: SdkVersion
    tags: Optional[List[str]] = None
    changelog: Optional[dict] = None
    ranking: Optional[int] = None
    dependencies: Optional[Dependencies] = None
    run_command: Optional[RunCommand] = None
    language: Optional[str] = 'cpp'
    pretty_name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'ProjectMetadata':
        # Convert nested dictionaries to their respective dataclass objects
        breakpoint()
        try:
            authors = [Author(**author) for author in data.get('authors', [])]
            sdk_version = SdkVersion(**data['sdk_version'])
            project_type = ProjectType(data['project_type'])
        except Exception as e:
            print(f"Error parsing required fields for {data.get('metadata_path', 'unknown')}: {e}")
        
        if 'dependencies' in data:
            deps = data['dependencies']
            hardware = [HardwareDescriptor(**hw) for hw in deps.get('hardware', [])]
            gxf = [VersionedDependency(**ext) for ext in deps.get('gxf_extensions', [])]
            dependencies = Dependencies(
                data=deps.get('data'),
                gxf_extensions=gxf,
                hardware=hardware
            )
            data['dependencies'] = dependencies
            
        if 'run_command' in data:
            data['run_command'] = RunCommand(**data['run_command'])
            
        return cls(
            project_type=project_type,
            authors=authors,
            sdk_version=sdk_version,
            **{k: v for k, v in data.items() if k not in ['authors', 'sdk_version']}
        )

    @classmethod
    def from_file(cls, metadata_filepath: Path) -> list['ProjectMetadata']:
        with open(metadata_filepath) as f:
            data = json.load(f)
            data['metadata_path'] = metadata_filepath
            if type(data) == dict:
                data = [data]
        return [cls.from_dict(d) for d in data]
    
    @property
    def project_root(self) -> Path:
        """
        Get the root directory for the project
        The project root is either
        1. The parent directory containing "cpp" and/or "python" language implementation folders, or
        2. If no language folders exist, the directory containing the metadata.json file.
        """
        metadata_dir = self.metadata_filepath.parent
        if (metadata_dir / "cpp").is_dir() or (metadata_dir / "python").is_dir():
            return metadata_dir
        return metadata_dir

    @property
    def project_language_dir(self) -> Path:
        """
        Get the language implementation directory for the project
        """
        return self.project_root
    
    @property
    def app_id(self) -> str:
        """
        Get the application ID for the project
        """
        return f"{self.name}.{self.language}"
        

# def get_pkg_dir(pkg_name: str, script_dir: Path) -> Path:
#     """Get source path for a given package according to HoloHub convention"""
#     if not pkg_name:
#         fatal("Missing package name argument for get_pkg_dir")
        
#     holohub_pkg_source = script_dir / "pkg" / pkg_name
    
#     # Check if the package is in a subdirectory
#     if not holohub_pkg_source.is_dir():
#         sub_pkg_paths = list(script_dir.glob(f"pkg/*/{pkg_name}"))
#         if sub_pkg_paths:
#             holohub_pkg_source = sub_pkg_paths[0]
            
#     if not holohub_pkg_source.is_dir():
#         fatal(f"Could not find package {pkg_name}")
        
#     return holohub_pkg_source
