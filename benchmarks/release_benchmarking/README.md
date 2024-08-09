# Release Benchmarking Guide

This tutorial provides a simplified interface to evaluate Holoscan SDK performance on two
commonly visited HoloHub applications.

# Getting Started

Both the Endoscopy Tool Tracking and the Multi-AI Ultrasound applications use the
HoloHub base container.

```
# Build the container
dev_container build

# Launch the dev environment
dev_container launch

# Build the applications in benchmarking mode
run build endoscopy_tool_tracking --benchmark
run build multiai_ultrasound --benchmark

# Run the benchmarking script to collect performance logs in the `./output` directory
run launch release_benchmarking
```

# Summarizing and Presenting Data

TODO
