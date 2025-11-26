"""
Stable Raft-style leader election demo.
Multiprocessing-safe logging for CSV output.
"""

import time
import random
from multiprocessing import Process, Queue, Value, Manager
from src.utils.metrics import Logger, now

ELECTION_TIMEOUT_MIN = 0.12
ELECTION_TIMEOUT_MAX = 0.28
FOLLOWER_EXIT_DELAY = 0.2   # how long followers wait after leader chosen

class Server(Process):
    def __init__(self, id, queues, result_q, log_list, stop_flag):
        super().__init__()
        self.id = id
        self.queues = queues      # dict id -> Queue
        self.inbox = queues[id]
        self.result_q = result_q
        self.log_list = log_list  # multiprocessing.Manager().list()
        self.stop_flag = stop_flag

    def safe_log(self, **kwargs):
        """Append log entry to shared list (multiprocess-safe)."""
        row = {"timestamp": now()}
        row.update(kwargs)
        self.log_list.append(row)

    def broadcast(self, msg):
        for qid, q in self.queues.items():
            if qid != self.id:
                q.put(msg)
                self.safe_log(event="send", src=self.id, dst=qid,
                              msg_type=msg[0], term=msg[1])

    def run(self):
        timeout = random.uniform(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)
        last_hb = time.time()
        term = 0
        voted_for = None

        while True:
            if self.stop_flag.value == 1:
                time.sleep(FOLLOWER_EXIT_DELAY)
                return

            try:
                m = self.inbox.get(timeout=0.02)
            except:
                m = None

            if m:
                typ, t, src = m
                if typ == "HEARTBEAT":
                    last_hb = time.time()
                elif typ == "VOTE_REQ":
                    if voted_for is None or voted_for == src:
                        voted_for = src
                        self.queues[src].put(("VOTE", t, self.id))
                        self.safe_log(event="vote", src=self.id, dst=src, term=t)

            # election timeout
            if time.time() - last_hb > timeout:
                term += 1
                votes = 1
                voted_for = self.id
                self.broadcast(("VOTE_REQ", term, self.id))

                # small vote collection window
                end_time = time.time() + 0.1
                while time.time() < end_time:
                    try:
                        r = self.inbox.get_nowait()
                        if r[0] == "VOTE" and r[1] == term:
                            votes += 1
                    except:
                        pass

                if votes > len(self.queues) // 2:
                    self.safe_log(event="elected", leader=self.id, term=term)
                    self.result_q.put((self.id, term, now()))
                    for _ in range(5):
                        self.broadcast(("HEARTBEAT", term, self.id))
                        time.sleep(0.03)
                    self.stop_flag.value = 1
                    return

                # failed election -> reset
                last_hb = time.time()
                timeout = random.uniform(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)


def run(n=5):
    os_queues = {i: Queue() for i in range(n)}
    result_q = Queue()
    stop_flag = Value("i", 0)

    manager = Manager()
    log_list = manager.list()  # shared list for logging

    servers = [Server(i, os_queues, result_q, log_list, stop_flag) for i in range(n)]

    for s in servers:
        s.start()

    # wait for leader
    leader_info = result_q.get()
    print("Leader elected:", leader_info)

    # allow processes to exit
    for s in servers:
        s.join(timeout=1)
        if s.is_alive():
            s.terminate()

    # save logs
    logger = Logger("docs/results/raft_log.csv")
    for row in log_list:
        logger.rows.append(row)
    logger.save()

    print("Raft demo finished. Log -> docs/results/raft_log.csv")


if __name__ == "__main__":
    run()
