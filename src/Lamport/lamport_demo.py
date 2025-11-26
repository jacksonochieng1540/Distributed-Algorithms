# src/lamport/lamport_demo.py
"""
Simple Lamport logical clocks demo.
Run: python src/lamport/lamport_demo.py
Logs to docs/results/lamport_log.csv
"""
import queue
import threading
import time
import random
from src.utils.metrics import Logger, now

class LamportClock:
    def __init__(self):
        self.time = 0

    def tick(self):
        self.time += 1
        return self.time

    def receive(self, other_time):
        self.time = max(self.time, other_time) + 1
        return self.time

class Node(threading.Thread):
    def __init__(self, node_id, inboxes, logger, events=6):
        super().__init__(daemon=True)
        self.node_id = node_id
        self.inboxes = inboxes
        self.inbox = inboxes[node_id]
        self.clock = LamportClock()
        self.logger = logger
        self.events = events

    def send(self, target):
        ts = self.clock.tick()
        msg = (self.node_id, ts, now())
        self.inboxes[target].put(msg)
        self.logger.log(event="send", src=self.node_id, dst=target, lamport=ts)

    def receive(self):
        try:
            sender, ts, send_time = self.inbox.get_nowait()
        except queue.Empty:
            return False
        local = self.clock.receive(ts)
        self.logger.log(event="recv", src=sender, dst=self.node_id, lamport_received=ts, lamport_local=local, latency=now() - send_time)
        return True

    def run(self):
        for _ in range(self.events):
            action = random.choice(["internal", "send", "recv"])
            if action == "internal":
                t = self.clock.tick()
                self.logger.log(event="internal", node=self.node_id, lamport=t)
            elif action == "send":
                choices = [i for i in range(len(self.inboxes)) if i != self.node_id]
                if choices:
                    target = random.choice(choices)
                    self.send(target)
            elif action == "recv":
                self.receive()
            time.sleep(random.uniform(0.05, 0.2))

def run(n_nodes=4, events_per_node=6):
    logger = Logger("docs/results/lamport_log.csv")
    inboxes = [queue.Queue() for _ in range(n_nodes)]
    nodes = [Node(i, inboxes, logger, events_per_node) for i in range(n_nodes)]
    for node in nodes:
        node.start()
    for node in nodes:
        node.join()
    logger.save()
    print("Lamport demo finished. Log -> docs/results/lamport_log.csv")

if __name__ == "__main__":
    run()
