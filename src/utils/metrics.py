# src/utils/metrics.py
import time
import csv
import os
import sys

def now():
    """High-resolution timestamp (seconds)."""
    return time.perf_counter()

class Logger:
    """Simple CSV logger collecting dict rows and writing them at the end."""
    def __init__(self, path):
        self.path = path
        self.rows = []

    def log(self, **kwargs):
        row = {"timestamp": now()}
        row.update(kwargs)
        self.rows.append(row)

    def save(self):
        if not self.rows:
            return
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        # ensure deterministic column order
        keys = sorted({k for r in self.rows for k in r.keys()})
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in self.rows:
                writer.writerow(r)

def bytes_of(obj):
    try:
        return sys.getsizeof(obj)
    except Exception:
        return 0
