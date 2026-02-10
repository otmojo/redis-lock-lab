import time as _time


import uuid
import os
import threading
from lock.watchdog import Watchdog

class RedisLock:
    def __init__(self, redis_client, resource_name, ttl_ms=30000):
        self.redis = redis_client
        self.watchdog = None
        # Enforce Key Naming Convention from README: lock:{resource}
        self.key = f"lock:{resource_name}"
        self.ttl_ms = int(ttl_ms)
        
        # Enforce Owner ID Format from README: UUID + process_id + thread_id
        self.owner_id = f"{uuid.uuid4()}:{os.getpid()}:{threading.get_ident()}"
        
        self.scripts = self._load_scripts()

    def _load_scripts(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_dir = os.path.join(base, "scripts")

        scripts = {}
        for name in ("acquire", "release", "renew"):
            path = os.path.join(script_dir, f"{name}.lua")
            with open(path, "r", encoding="utf-8") as f:
                scripts[name] = self.redis.register_script(f.read())
        return scripts

    def acquire(self):
        now_ms = int(_time.time() * 1000)

        ok = self.scripts["acquire"](
            keys=[self.key],
            args=[self.owner_id, self.ttl_ms, now_ms]
        ) == 1

        if ok:
            self.watchdog = Watchdog(self)
            self.watchdog.start()

        return ok

    def release(self):
        if self.watchdog:
            self.watchdog.stop()

        return self.scripts["release"](
            keys=[self.key],
            args=[self.owner_id]
        ) == 1

    
    
    def renew(self, ttl_ms=None):
        ttl = int(ttl_ms) if ttl_ms else self.ttl_ms
        now_ms = int(_time.time() * 1000)

        return self.scripts["renew"](
            keys=[self.key],
            args=[self.owner_id, ttl, now_ms]
        ) == 1
