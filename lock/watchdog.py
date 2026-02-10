import threading
import time
import random

class Watchdog(threading.Thread):
    def __init__(self, lock, interval_ms=300):
        super().__init__(daemon=True)
        self.lock = lock
        self.interval = interval_ms / 1000
        self.running = True

    def run(self):
        while self.running:
            time.sleep(self.interval)

            # === 故障注入点 1：模拟 GC / STW ===
            if random.random() < 0.05:
                time.sleep(self.lock.ttl_ms / 1000 * 1.5)

            ok = self.lock.renew()
            if not ok:
                self.stop()
                return

    def stop(self):
        self.running = False

