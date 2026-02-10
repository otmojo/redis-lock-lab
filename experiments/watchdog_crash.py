import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import redis
import time
import signal
from lock.redis_lock import RedisLock

def run():
    r = redis.Redis()
    key = "lock:watchdog:test"
    r.delete(key)

    lock = RedisLock(r, key, ttl_ms=1000)

    print("[A] acquiring lock")
    assert lock.acquire()

    print("[A] working 5s (watchdog active)")
    time.sleep(2)

    # === 故障注入点 2：kill 主线程 ===
    print("[A] force exit (Windows equivalent of SIGKILL)")
    os._exit(1)

if __name__ == "__main__":
    run()