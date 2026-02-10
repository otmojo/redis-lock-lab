-- KEYS[1]: lock_key
-- ARGV[1]: owner_id

local key = KEYS[1]
local owner = ARGV[1]

if redis.call("EXISTS", key) == 0 then
    return 0
end

local current_owner = redis.call("HGET", key, "owner")
if current_owner ~= owner then
    return 0
end

local count = redis.call("HINCRBY", key, "count", -1)
if count <= 0 then
    redis.call("DEL", key)
    return 1
else
    return 1
end
