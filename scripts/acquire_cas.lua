-- acquire_cas.lua
-- KEYS[1]: lock key
-- ARGV[1]: owner_id
-- ARGV[2]: ttl_ms
-- ARGV[3]: now_ms

local key   = KEYS[1]
local owner = ARGV[1]
local ttl   = tonumber(ARGV[2])
local now   = tonumber(ARGV[3])

local expire_at = now + ttl

if redis.call("EXISTS", key) == 0 then
    redis.call("HMSET", key,
        "owner", owner,
        "count", 1,
        "expire_at", expire_at
    )
    redis.call("PEXPIRE", key, ttl)
    return 1
end

local current_owner = redis.call("HGET", key, "owner")
local current_expire = tonumber(redis.call("HGET", key, "expire_at"))

-- reentrant
if current_owner == owner then
    redis.call("HINCRBY", key, "count", 1)
    redis.call("HSET", key, "expire_at", expire_at)
    redis.call("PEXPIRE", key, ttl)
    return 1
end

-- logical expired → steal
if current_expire ~= nil and now > current_expire then
    redis.call("HMSET", key,
        "owner", owner,
        "count", 1,
        "expire_at", expire_at
    )
    redis.call("PEXPIRE", key, ttl)
    return 1
end

return 0