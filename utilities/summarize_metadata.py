# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import glob
import json
import os
import sys
from enum import Enum
from itertools import chain

from collections import defaultdict
from dataclasses import dataclass

class ProjectType(Enum):
    APPLICATION = 0
    GXF_EXTENSION = 1
    OPERATOR = 2

@dataclass
class ProjectTypeData:
    project_type: ProjectType
    folder_name: str
    schema_name: str

    @property
    def schema_filepath(self) -> str:
        return f'{self.folder_name}/metadata.schema.json'

    @property
    def schema(self) -> dict:
        if not self.schema:
            with open(project_type_info.schema_filepath,'r') as file:
                self.schema = json.load(file)
        return self.schema

    def get_key(self, metadata:dict, key:str) -> object:
        return metadata[self.schema_name][key]

project_type_data = [
    ProjectTypeData(ProjectType.APPLICATION, 'applications', 'application'),
    ProjectTypeData(ProjectType.GXF_EXTENSION, 'gxf_extensions', 'gxf_extension'),
    ProjectTypeData(ProjectType.OPERATOR, 'operators', 'operator'),
]

metadata = defaultdict(dict)
aggregate_info = {k: defaultdict(list) for k in ['name', 'platforms', 'holoscan_sdk', 'gxf_version']}

# Ingest project metadata files
for project_type_info in project_type_data:
    project_type = project_type_info.project_type
    schema_name = project_type_info.schema_name
    
    metadata_files = glob.glob(f'{project_type_info.folder_name}/**/metadata.json')
    for filename in metadata_files:
        with open(filename,'r') as file:
            project_metadata = json.load(file)
        
        for key in aggregate_info:
            if key in project_metadata[schema_name].keys():
                aggregate_info[key][project_type].append(project_metadata[schema_name][key])

# Process specific fields
platform_counts = defaultdict(int)
for project_type in ProjectType:
    for platform_list in aggregate_info['platforms'][project_type]:
        for platform_str in platform_list:
            platform_counts[platform_str] += 1

print(platform_counts)

# Summarize
for k in aggregate_info:
    for project_type in aggregate_info[k]:
        print(f'{k} {str(project_type)}: {len(aggregate_info[k][project_type])}')


