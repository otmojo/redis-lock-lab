-- renew.lua
-- KEYS[1] : lock key
-- ARGV[1] : owner_id
-- ARGV[2] : ttl_ms
-- ARGV[3] : now_ms

local key = KEYS[1]
local owner = ARGV[1]
local ttl = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

if not now then
    return 0
end

if redis.call("EXISTS", key) == 0 then
    return 0
end

local current_owner = redis.call("HGET", key, "owner")
if current_owner ~= owner then
    return 0
end

local expire_at = tonumber(redis.call("HGET", key, "expire_at"))
if not expire_at then
    return 0
end

-- when the lock is already logically expired
if expire_at <= now then
    return 0
end

local new_expire = now + ttl
redis.call("HSET", key, "expire_at", new_expire)
redis.call("PEXPIRE", key, ttl)

return 1