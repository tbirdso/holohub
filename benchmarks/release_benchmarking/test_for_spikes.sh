#!/usr/bin/bash

# Test script to attempt to recreate observed max latency "spikes"

./run build multiai_ultrasound --benchmark

headless=false
realtime=false
# APP_CONFIG_PATH=./build/endoscopy_tool_tracking/applications/endoscopy_tool_tracking/cpp/endoscopy_tool_tracking.yaml
APP_CONFIG_PATH=./build/multiai_ultrasound/applications/multiai_ultrasound/cpp/multiai_ultrasound.yaml
sed -i "s/^  headless: .*/  headless: ${headless}/" ${APP_CONFIG_PATH}
sed -i "s/^  realtime: .*/  realtime: ${realtime}/" ${APP_CONFIG_PATH}

RUN_COUNT=10
MESSAGE_COUNT=1000
INSTANCE_COUNT=3
LOG_DIR=$(pwd)/logs/benchmarking_$(date +%Y%m%d-%H%M%S)
set -x
python -m benchmark --sched greedy -i ${INSTANCE_COUNT} -m ${MESSAGE_COUNT} -r ${RUN_COUNT} -a multiai_ultrasound -d ${LOG_DIR}
set +x
mkdir -p ${LOG_DIR}/processed && pushd ${LOG_DIR}/processed

groups=""
for instances in $(seq 1 ${RUN_COUNT}); do
    groups+="-g "
    for file in $(find .. -name logger_greedy_${instances}_\*.log | sort); do
        groups+="${file} "
    done
done
python -m analyze --save-csv --no-display-graphs --max --avg --min -p 99 ${groups}
python -m generate_bar_graph ./max_values.csv --app "Multi-AI Ultrasound" --quiet

popd
