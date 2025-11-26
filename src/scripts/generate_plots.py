# src/scripts/generate_plots.py
import pandas as pd
import matplotlib.pyplot as plt
import os

os.makedirs("docs/results", exist_ok=True)

# Lamport: histogram of latencies if present
try:
    df = pd.read_csv("docs/results/lamport_log.csv")
    recv = df[df["event"] == "recv"]
    if not recv.empty:
        plt.hist(recv["latency"], bins=20)
        plt.title("Lamport message latency (s)")
        plt.xlabel("seconds")
        plt.savefig("docs/results/lamport-log.png")
        plt.clf()
        print("Saved docs/results/lamport-log.png")
except Exception as e:
    print("Lamport plot error:", e)

# Raft: count elected events by leader if present
try:
    df = pd.read_csv("docs/results/raft_log.csv")
    elected = df[df["event"] == "elected"]
    if not elected.empty:
        counts = elected["leader"].value_counts()
        counts.plot(kind="bar")
        plt.title("Raft elected counts")
        plt.savefig("docs/results/raft-election-chart.png")
        plt.clf()
        print("Saved docs/results/raft-election-chart.png")
except Exception as e:
    print("Raft plot error:", e)

# MapReduce: scatter elapsed vs chunks if present
try:
    df = pd.read_csv("docs/results/mapreduce_log.csv")
    if not df.empty:
        plt.scatter(df["chunks"], df["elapsed"])
        plt.title("MapReduce elapsed vs chunks")
        plt.xlabel("chunks")
        plt.ylabel("elapsed (s)")
        plt.savefig("docs/results/mapreduce-throughput.png")
        plt.clf()
        print("Saved docs/results/mapreduce-throughput.png")
except Exception as e:
    print("MapReduce plot error:", e)

# Load Balancer: plot processed (note: we logged 'run' rows only)
try:
    df = pd.read_csv("docs/results/load_balancer_log.csv")
    if not df.empty:
        runs = df[df["event"] == "run"]
        if not runs.empty:
            runs.plot(x="mode", y="processed", kind="bar")
            plt.title("Load balancer processed tasks by mode")
            plt.savefig("docs/results/load-balancer-stats.png")
            plt.clf()
            print("Saved docs/results/load-balancer-stats.png")
except Exception as e:
    print("Load balancer plot error:", e)
