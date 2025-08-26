#!/bin/bash
# Convenience script to run the build installer from the project root
cd "$(dirname "$0")" && exec scripts/unix/build_installer.sh "$@"
