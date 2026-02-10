import unittest
import fakeredis
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lock.redis_lock import RedisLock

class TestRedisLock(unittest.TestCase):
    def setUp(self):
        self.server = fakeredis.FakeServer()
        self.redis = fakeredis.FakeRedis(server=self.server)
        self.key = "test_lock"

    def test_acquire_release(self):
        lock = RedisLock(self.redis, self.key, ttl_ms=1000)
        self.assertTrue(lock.acquire(), "Should acquire lock")
        self.assertIsNotNone(self.redis.get(self.key), "Key should exist")
        self.assertTrue(lock.release(), "Should release lock")
        self.assertIsNone(self.redis.get(self.key), "Key should be gone")

    def test_mutual_exclusion(self):
        lock1 = RedisLock(self.redis, self.key, ttl_ms=1000)
        lock2 = RedisLock(self.redis, self.key, ttl_ms=1000)
        
        self.assertTrue(lock1.acquire())
        self.assertFalse(lock2.acquire(), "Should not acquire locked resource")
        
        lock1.release()
        self.assertTrue(lock2.acquire(), "Should acquire after release")

    def test_renew(self):
        lock = RedisLock(self.redis, self.key, ttl_ms=1000)
        lock.acquire()
        
        # Manually reduce TTL to simulate time passing (hacky with fakeredis?)
        # Or just check if renew resets it.
        # Let's just call renew.
        
        success = lock.renew()
        self.assertTrue(success)
        pttl = self.redis.pttl(self.key)
        self.assertTrue(900 < pttl <= 1000)

if __name__ == '__main__':
    unittest.main()
