# src/mapreduce/mapreduce_demo.py
"""
Simple MapReduce (word count) demo using multiprocessing.
Run: python src/mapreduce/mapreduce_demo.py
Logs to docs/results/mapreduce_log.csv
"""
from multiprocessing import Pool, cpu_count
from collections import Counter
import os
import time
from src.utils.metrics import Logger

def map_fn(text_chunk):
    words = []
    for w in text_chunk.split():
        cleaned = "".join(ch for ch in w.lower() if ch.isalpha())
        if cleaned:
            words.append(cleaned)
    return Counter(words)

def reduce_fn(counter_list):
    total = Counter()
    for c in counter_list:
        total.update(c)
    return total

def chunkify(path, n_chunks):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    words = text.split()
    if not words:
        return []
    chunk_size = max(1, len(words) // n_chunks)
    chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

def run(path="examples/sample_text.txt", workers=None):
    workers = workers or min(cpu_count(), 4)
    logger = Logger("docs/results/mapreduce_log.csv")
    if not os.path.exists(path):
        # create small sample
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(("hello world\n" * 2000))
    chunks = chunkify(path, workers)
    t0 = time.perf_counter()
    with Pool(workers) as p:
        mapped = p.map(map_fn, chunks)
    shuffled = mapped  # as list of Counters, we can reduce directly
    result = reduce_fn(shuffled)
    t1 = time.perf_counter()
    elapsed = t1 - t0
    logger.log(event="mapreduce_run", workers=workers, chunks=len(chunks), elapsed=elapsed, unique_words=len(result))
    logger.save()
    print("MapReduce finished. Unique words:", len(result))
    print("Elapsed:", elapsed)
    print("MapReduce log -> docs/results/mapreduce_log.csv")
    # print top 10
    for w, c in result.most_common(10):
        print(f"{w:12} : {c}")

if __name__ == "__main__":
    run()
