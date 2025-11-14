# HoloHub Post-Installation Setup Scripts

## Overview

This folder contains a collection of scripts that can be run locally or in a container build
to install "extra" dependencies for common development tasks.

These scripts are recommended for advanced, specific development use cases.

## Usage

To view available scripts:
```bash
./holohub setup --list-scripts
```

To add "extras" to a development container with HoloHub CLI:
```bash
./holohub build-container [my-project] \
    --extra-scripts [my-script-1] \
    --extra-scripts [my-script-2] ...
```

To add "extras" to the local environment:
```bash
./holohub setup --scripts [my-script-1] --scripts [my-script-2] ...
```

## Available Scripts

- `coverage`: Common dependencies for code coverage analysis and reporting
- `xvfb`: Common dependencies for display testing on headless machines
- `holoscan-dev`: Install latest Holoscan SDK Debian and Python components in any development container
