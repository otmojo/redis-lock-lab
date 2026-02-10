-- KEYS[1]: lock_key
-- ARGV[1]: owner_id
-- ARGV[2]: ttl_ms

local key = KEYS[1]
local owner = ARGV[1]
local ttl = tonumber(ARGV[2])

if redis.call("EXISTS", key) == 0 then
    redis.call("HMSET", key, "owner", owner, "count", 1)
    redis.call("PEXPIRE", key, ttl)
    return 1
end

local current_owner = redis.call("HGET", key, "owner")
if current_owner == owner then
    redis.call("HINCRBY", key, "count", 1)
    redis.call("PEXPIRE", key, ttl)
    return 1
end

return 0
