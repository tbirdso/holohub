#!/bin/bash
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
set -e

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
TOP=$(realpath "${SCRIPT_DIR}/../..")

is_igx() {
    if [[ -f /etc/nv_tegra_release ]] || [[ -f /etc/igx-release ]]; then
        return 0
    fi
    return 1
}

run_command() {
    local status=0
    local cmd="$*"

    if [ "${DO_DRY_RUN}" != "true" ]; then
        echo -e "${YELLOW}[command]${NOCOLOR} ${cmd}"
    else
        echo -e "${YELLOW}[dryrun]${NOCOLOR} ${cmd}"
    fi

    [ "$(echo -n "$@")" = "" ] && return 1 # return 1 if there is no command available

    if [ "${DO_DRY_RUN}" != "true" ]; then
        eval "$@"
        status=$?
    fi
    return $status
}

run_benchmark() {
    ARGS=("$@")
    local runs=3
    local instances=3
    local messages=1000
    local scheduler=greedy
    local output=""
    local headless=false
    local realtime=false
    local app_config=""
    local app=""

    for i in "${!ARGS[@]}"; do
        arg="${ARGS[i]}"
        if [[ $skipnext == "1" ]]; then
            skipnext=0
        elif [[ "$arg" == "--help" ]]; then
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --app <str>         Application to benchmark"
            echo "  --app_config <str>  Application configuration file"
            echo "  --runs <int>        Number of runs"
            echo "  --instances <int>   Number of instances"
            echo "  --messages <int>    Number of messages"
            echo "  --scheduler <str>   Scheduler to use"
            echo "  --output <str>      Output directory"
            echo "  --headless          Run in headless mode"
            echo "  --realtime          Run in real-time mode"
            exit 0
        elif [ "$arg" = "--app" ]; then
            app="${ARGS[i + 1]}"
            skipnext=1
        elif [ "$arg" = "--app_config" ]; then
            app_config="${ARGS[i + 1]}"
            skipnext=1
        elif [ "$arg" = "--runs" ]; then
            runs="${ARGS[i + 1]}"
            skipnext=1
        elif [ "$arg" = "--instances" ]; then
            instances="${ARGS[i + 1]}"
            skipnext=1
        elif [ "$arg" = "--messages" ]; then
            messages="${ARGS[i + 1]}"
            skipnext=1
        elif [ "$arg" = "--scheduler" ]; then
            scheduler="${ARGS[i + 1]}"
            skipnext=1
        elif [ "$arg" = "--output" ]; then
            output="${ARGS[i + 1]}"
            skipnext=1
        elif [ "$arg" = "--headless" ]; then
            headless=true
        elif [ "$arg" = "--realtime" ]; then
            realtime=true
        fi
    done

    if [[ -z "${app_config}" || ! -f "${app_config}" ]]; then
        echo "No application configuration filepath specified with '--app_config'"
        exit 1
    fi
    output=${output:-"${SCRIPT_DIR}/output/${app}_${runs}_${instances}_${messages}_${scheduler}_${headless}_${realtime}"}
    mkdir -p $(dirname ${output})

    sed -i "s/^  headless: .*/  headless: ${headless}/" ${APP_CONFIG_PATH}
    sed -i "s/^  realtime: .*/  realtime: ${realtime}/" ${APP_CONFIG_PATH}

    set -x
    run_command python \
        ${TOP}/benchmarks/holoscan_flow_benchmarking/benchmark.py \
        -a ${app} \
        -r ${runs} \
        -i ${instances} \
        -m ${messages} \
        --sched ${scheduler} \
        -d ${output}
    set +x
}

benchmark_endoscopy_tool_tracking() {
    APP_CONFIG_PATH=${TOP}/applications/endoscopy_tool_tracking/cpp/endoscopy_tool_tracking.yaml

    if is_igx; then
        instance_range=$(seq 1 3)
    else
        instance_range=$(seq 1 8)
    fi

    # Real time
    for instances in ${instance_range}; do
        run_benchmark \
            --app endoscopy_tool_tracking \
            --app_config ${APP_CONFIG_PATH} \
            --instances ${instances} \
            --realtime
    done

    # Real time disabled
    for instances in ${instance_range}; do
        run_benchmark \
            --app endoscopy_tool_tracking \
            --app_config ${APP_CONFIG_PATH} \
            --instances ${instances}
    done

    # Real time disabled + visualizations disabled
    for instances in ${instance_range}; do
        run_benchmark \
            --app endoscopy_tool_tracking \
            --app_config ${APP_CONFIG_PATH} \
            --instances ${instances} \
            --headless
    done
}

benchmark_multiai_ultrasound() {
    APP_CONFIG_PATH=${TOP}/applications/multiai_ultrasound/cpp/multiai_ultrasound.yaml

    if is_igx; then
        instance_range=$(seq 1 2)
    else
        instance_range=$(seq 1 3)
    fi

    # Real time
    for instances in ${instance_range}; do
        run_benchmark \
            --app multiai_ultrasound \
            --app_config ${APP_CONFIG_PATH} \
            --instances ${instances} \
            --realtime
    done

    # Real time disabled + visualizations disabled
    for instances in ${instance_range}; do
        run_benchmark \
            --app multiai_ultrasound \
            --app_config ${APP_CONFIG_PATH} \
            --instances ${instances} \
            --headless
    done
}

pushd ${TOP}
benchmark_endoscopy_tool_tracking
benchmark_multiai_ultrasound
popd
