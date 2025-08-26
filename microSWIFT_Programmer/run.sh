#!/bin/bash
# Convenience script to run from source on macOS/Linux
cd "$(dirname "$0")"
exec ./scripts/run/run_from_source.sh "$@"
