#!/bin/bash

script_path="./run.sh"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <config_file> <num_times>"
    exit 1
fi

config_file="$1"
num_times="$2"

for ((i=1; i<=$num_times; i++)); do
    echo "Running iteration $i with config file: $config_file"
    bash "$script_path" "$config_file"
done
