#!/bin/bash
if [ -z "$1" ]; then
  echo "Usage: $0 <linux / macos>"
  exit 1
fi

case "$1" in
  linux)
    echo "Starting Seyoawe Community Edition for Linux..."
    ./seyoawe.linux
    ;;
  macos)
    echo "Starting Seyoawe Community Edition for macOS..."
    ./seyoawe.macos.arm
    ;;
  *)
    echo "Invalid argument. Use 'linux' or 'macos'."
    exit 1
    ;;
esac