import time
import redis
import sys
import os

# ensure project root in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lock.redis_lock import RedisLock
from metrics.collector import Metrics


LOCK_NAME = "resource"


def run_experiment(ttl_ms: int, work_time_ms: int) -> dict:
    """
    TTL Misjudge Experiment

    Hypothesis:
        If work_time > ttl, the lock may expire while still in critical section.

    Returns:
        metrics dict
    """
    r = redis.Redis(host="localhost", port=6379, db=0)
    r.ping()

    lock_key = f"lock:{LOCK_NAME}"

    # 1. reset environment
    r.delete(lock_key)
    Metrics.reset()

    lock = RedisLock(r, LOCK_NAME, ttl_ms=ttl_ms)

    metrics = {
        "ttl_ms": ttl_ms,
        "work_time_ms": work_time_ms,
        "acquire_latency_ms": None,
        "expired_while_working": False,
        "still_owner_after_work": False,
        "lock_stolen_count": 0,
    }

    # 2. acquire
    t0 = time.time()
    acquired = lock.acquire()
    t1 = time.time()

    metrics["acquire_latency_ms"] = int((t1 - t0) * 1000)

    if not acquired:
        Metrics.record("acquire_failed", 1)
        return metrics

    # 3. critical section (deterministic)
    time.sleep(work_time_ms / 1000.0)

    # 4. oracle check (Redis truth)
    lock_data = r.hgetall(lock_key)

    if not lock_data:
        # key disappeared => TTL expired
        metrics["expired_while_working"] = True
        Metrics.record("ttl_expired_while_working", 1)

    elif lock_data.get(b"owner") != lock.owner_id.encode():
        # key exists but owner changed
        metrics["lock_stolen_count"] = 1
        Metrics.record("lock_stolen_count", 1)

    else:
        metrics["still_owner_after_work"] = True
        Metrics.record("still_owner_after_work", 1)

    # 5. best-effort release
    lock.release()

    return metrics


if __name__ == "__main__":
    print("\n=== TTL Misjudge Experiment ===")

    # Case 1: Safe (work < TTL)
    result_safe = run_experiment(ttl_ms=2000, work_time_ms=1000)
    print("[SAFE]", result_safe)

    # Case 2: Misjudge (work > TTL)
    result_unsafe = run_experiment(ttl_ms=1000, work_time_ms=2000)
    print("[MISJUDGE]", result_unsafe)