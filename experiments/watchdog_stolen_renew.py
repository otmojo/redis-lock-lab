import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import time
import threading
import redis
from lock.redis_lock import RedisLock

REDIS_URL = "redis://127.0.0.1:6379/0"
LOCK_NAME = "watchdog:stolen"
TTL_MS = 1000


def client_a():
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    lock = RedisLock(r, LOCK_NAME, ttl_ms=TTL_MS)

    print("[A] acquire lock")
    ok = lock.acquire()
    print("[A] acquired =", ok)

    print("[A] sleep 3s (TTL=1s, watchdog running)")
    time.sleep(3)

    print("[A] still alive, not releasing")
    time.sleep(5)


def client_b():
    time.sleep(1.5) # wait for A s lock to acquire and sleep

    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    lock = RedisLock(r, LOCK_NAME, ttl_ms=TTL_MS)

    print("[B] try acquire")
    ok = lock.acquire()
    print("[B] acquired =", ok)

    for i in range(5):
        owner = r.hget(f"lock:{LOCK_NAME}", "owner")
        ttl = r.pttl(f"lock:{LOCK_NAME}")
        print(f"[B] t={i}s owner={owner} ttl={ttl}")
        time.sleep(1)


def run():
    t1 = threading.Thread(target=client_a)
    t2 = threading.Thread(target=client_b)

    t1.start()
    t2.start()

    t1.join()
    t2.join()


if __name__ == "__main__":
    run()