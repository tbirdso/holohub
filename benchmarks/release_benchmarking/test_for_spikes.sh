#!/usr/bin/bash

# Test script to attempt to recreate observed max latency "spikes"

RUN_COUNT=2
MESSAGE_COUNT=10000
INSTANCE_COUNT=8
LOG_DIR=$(pwd)/logs/benchmarking_$(date +%Y%m%d-%H%M%S)
python -m benchmark --sched greedy -i ${INSTANCE_COUNT} -m ${MESSAGE_COUNT} -r ${RUN_COUNT} -a endoscopy_tool_tracking -d ${LOG_DIR}
mkdir -p ${LOG_DIR}/processed && pushd ${LOG_DIR}/processed

groups=""
for instances in $(seq 1 ${RUN_COUNT}); do
    for file in $(find .. -name logger_greedy_${instances}_\*.log | sort); do
        groups+="-g ${file} "
    done
done
python -m analyze --save-csv --no-display-graphs --max --avg --min -p 99 ${groups}
python -m generate_bar_graph ./max_values.csv --app "Endoscopy Tool Tracking" --quiet

popd
