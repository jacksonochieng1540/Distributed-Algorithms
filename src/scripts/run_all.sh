#!/usr/bin/env bash
set -e
export PYTHONPATH=.

echo "Ensure docs/results exists"
mkdir -p docs/results

echo "Running Lamport demo..."
python src/lamport/lamport_demo.py

echo "Running Raft demo..."
python src/raft/raft_election_demo.py

echo "Running MapReduce demo..."
python src/mapreduce/mapreduce_demo.py

echo "Running Load Balancer demo..."
python src/load_balancer/load_balancer_demo.py

echo "All demos finished. Logs are in docs/results/"
