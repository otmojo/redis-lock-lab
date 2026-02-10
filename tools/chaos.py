import time
import random

class Chaos:
    @staticmethod
    def sleep_random(min_ms, max_ms):
        """
        Simulate processing time or GC pause.
        """
        duration = random.uniform(min_ms, max_ms) / 1000.0
        time.sleep(duration)
    
    @staticmethod
    def inject_latency(ms):
        """
        Simulate network latency.
        """
        time.sleep(ms / 1000.0)
