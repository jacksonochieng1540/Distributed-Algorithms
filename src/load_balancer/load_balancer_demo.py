"""
Stable load balancer demo with Round Robin + Least Connections.
Safe multiprocessing version.
Run: python -m src.load_balancer.load_balancer_demo
"""

import time
import random
import threading
from multiprocessing import Process, Queue, Manager
from src.utils.metrics import Logger


def worker_process(worker_id, task_q, stats):
    """
    Worker receives tasks and updates stats safely using Manager().
    """
    while True:
        task = task_q.get()
        if task is None:
            break

        cost = task.get("cost", 0.02)
        start = time.perf_counter()
        time.sleep(cost)
        end = time.perf_counter()

        # Safe updates
        stats[worker_id]["processed"].set(stats[worker_id]["processed"].get() + 1)
        stats[worker_id]["total_time"].set(
            stats[worker_id]["total_time"].get() + (end - start)
        )


def make_stats(manager, n):
    """Create safe stats structure with Manager().dict of Manager().Value."""
    stats = manager.dict()
    for i in range(n):
        stats[i] = {
            "processed": manager.Value("i", 0),
            "total_time": manager.Value("d", 0.0),
            "conn": manager.Value("i", 0),
        }
    return stats


class LoadBalancer:
    def __init__(self, n_workers=4, mode="round_robin"):
        self.n = n_workers
        self.mode = mode
        self.task_queues = [Queue() for _ in range(n_workers)]
        self.manager = Manager()
        self.stats = make_stats(self.manager, n_workers)

        # spawn worker processes
        self.procs = [
            Process(target=worker_process, args=(i, self.task_queues[i], self.stats))
            for i in range(n_workers)
        ]
        for p in self.procs:
            p.start()

        self.rr_idx = 0

    def dispatch(self, task):
        """Dispatches a task using RR or LC with safe counters."""
        if self.mode == "round_robin":
            idx = self.rr_idx % self.n
            self.rr_idx += 1

        elif self.mode == "least_conn":
            idx = min(
                range(self.n),
                key=lambda i: self.stats[i]["conn"].get()
            )
        else:
            idx = random.randrange(self.n)

        # increment conn safely
        self.stats[idx]["conn"].set(self.stats[idx]["conn"].get() + 1)

        # send task
        self.task_queues[idx].put(task)

        # simulate completion: decrement conn later
        def release(i, delay):
            time.sleep(delay)
            self.stats[i]["conn"].set(self.stats[i]["conn"].get() - 1)

        threading.Thread(
            target=release,
            args=(idx, task.get("cost", 0.02)),
            daemon=True
        ).start()

    def stop(self):
        """Stop workers and return normal Python stats dict."""
        for q in self.task_queues:
            q.put(None)
        for p in self.procs:
            p.join()

        # return plain dict
        output = {}
        for i in range(self.n):
            output[i] = {
                "processed": self.stats[i]["processed"].get(),
                "total_time": self.stats[i]["total_time"].get(),
            }
        return output


def run(num_workers=4, num_tasks=200):
    logger = Logger("docs/results/load_balancer_log.csv")

    tasks = [{"id": i, "cost": random.uniform(0.005, 0.03)}
             for i in range(num_tasks)]

    # ROUND ROBIN
    lb_rr = LoadBalancer(n_workers=num_workers, mode="round_robin")
    t0 = time.perf_counter()
    for t in tasks:
        lb_rr.dispatch(t)
        time.sleep(0.002)
    stats_rr = lb_rr.stop()
    t1 = time.perf_counter()

    logger.log(
        event="run",
        mode="round_robin",
        elapsed=(t1 - t0),
        processed=sum(s["processed"] for s in stats_rr.values())
    )

    # ----------------------------------------------------

    # LEAST CONNECTIONS
    lb_lc = LoadBalancer(n_workers=num_workers, mode="least_conn")
    t0 = time.perf_counter()
    for t in tasks:
        lb_lc.dispatch(t)
        time.sleep(0.002)
    stats_lc = lb_lc.stop()
    t1 = time.perf_counter()

    logger.log(
        event="run",
        mode="least_conn",
        elapsed=(t1 - t0),
        processed=sum(s["processed"] for s in stats_lc.values())
    )

    logger.save()

    print("\n--- ROUND ROBIN ---")
    print(stats_rr)
    print("\n--- LEAST CONNECTIONS ---")
    print(stats_lc)
    print("\nLog saved → docs/results/load_balancer_log.csv")


if __name__ == "__main__":
    run()
