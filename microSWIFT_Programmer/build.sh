#!/bin/bash
# Convenience script to run the macOS build from root directory
cd "$(dirname "$0")"
exec ./scripts/build/build_macos.sh "$@"
