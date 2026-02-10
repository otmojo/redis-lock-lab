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
LOCK_NAME = "watchdog:pause"
TTL_MS = 1000


def client_a():
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    lock = RedisLock(r, LOCK_NAME, ttl_ms=TTL_MS)

    print("[A] acquire")
    lock.acquire()

    print("[A] watchdog stop manually")
    lock.watchdog.stop()

    print("[A] sleep 2s (lock should expire)")
    time.sleep(2)

    print("[A] try renew AFTER losing lock")
    ok = lock.renew()
    print("[A] renew result =", ok)


def client_b():
    time.sleep(1.2)

    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    lock = RedisLock(r, LOCK_NAME, ttl_ms=TTL_MS)

    print("[B] acquire")
    ok = lock.acquire()
    print("[B] acquired =", ok)

    for i in range(3):
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