#!/bin/bash

# Set the environment variable, replace 10 with your desired number
export NUM_ITERATIONS=1000

# Run the Python script for each value from 1 to NUM_ITERATIONS
for ((i=1;i<=NUM_ITERATIONS;i++)); do
   output=$(python ./run_example.py /Users/e550705/workspaces/PyVRP/examples/data/outbound_distance_new_${i}.vrp | grep OUT | sed 's/\[//g' | sed 's/\]//g')
   output=$(echo "$i $output"|sed 's/OUT//g')
   echo $output
done
