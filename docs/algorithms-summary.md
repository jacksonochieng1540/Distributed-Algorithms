# Algorithms Summary

This document summarizes the algorithms implemented in `src/`.

## Lamport Logical Clocks
- Purpose: causal ordering of events
- Demo: `src/lamport/lamport_demo.py`

## Raft-style Leader Election
- Purpose: elect a leader using randomized timeouts and voting
- Demo: `src/raft/raft_election_demo.py`

## MapReduce (Word Count)
- Purpose: show map, shuffle and reduce stages with multiprocessing
- Demo: `src/mapreduce/mapreduce_demo.py`

## Load Balancer (Round-robin & Least-connections)
- Purpose: dispatch tasks to workers and measure fairness and latency
- Demo: `src/load_balancer/load_balancer_demo.py`
