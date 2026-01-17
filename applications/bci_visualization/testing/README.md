# BCI Visualization Integration Test

This directory contains integration test assets for the BCI Visualization application.

## Test Overview

The integration test validates:
1. **End-to-end execution**: The application runs without unexpected errors
2. **Frame validation**: At least 10 rendered frames match expected reference images

## Reference Frames

The PNG files (`0001.png` through `0010.png`) are reference frames used for validation.
These frames are compared against the test output using the `video_validation.py` utility.

### Generating Reference Frames

Use the provided script to generate or update reference frames:

```bash
# From the holohub root directory
./applications/bci_visualization/testing/generate_reference_frames.sh
```

Or with custom paths:
```bash
./applications/bci_visualization/testing/generate_reference_frames.sh [BUILD_DIR] [DATA_DIR]
```

#### Prerequisites

1. Download the BCI visualization data:
   ```bash
   hf download KernelCo/holohub_bci_visualization --repo-type dataset --local-dir data/bci_visualization
   ```

2. Build the application with testing enabled:
   ```bash
   ./run build bci_visualization --configure-args "-DBUILD_TESTING=ON"
   ```

The script will:
1. Run the application with recording enabled (10 frames)
2. Convert the recorded GXF entities to PNG images
3. Copy the first 10 frames as reference images to this directory

## Test Configuration

The test is configured in `CMakeLists.txt` and includes:
- A patched version of the application (`bci_visualization.patch`) that enables:
  - Frame count limiting (10 frames)
  - Render buffer output from HolovizOp
  - VideoStreamRecorder for capturing output
- YAML configuration modifications for testing
- Frame validation using `utilities/video_validation.py`

## Running the Tests

```bash
# Build with testing enabled
./run build bci_visualization --configure-args "-DBUILD_TESTING=ON"

# Run the tests
cd build
ctest -R bci_visualization -V
```
