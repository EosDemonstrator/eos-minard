from redis import StrictRedis
from itertools import chain

redis = StrictRedis()

HMINCRBY = """
local f
for _, key in ipairs(KEYS) do
    for i, v in ipairs(ARGV) do
        if i % 2 == 1 then
            f = v
        else
            redis.call('HINCRBY', key, tostring(f), tonumber(v))
        end
    end
end
return true
"""

HMINCRBYFLOAT = """
local f
for _, key in ipairs(KEYS) do
    for i, v in ipairs(ARGV) do
        if i % 2 == 1 then
            f = v
        else
            redis.call('HINCRBYFLOAT', key, tostring(f), tonumber(v))
        end
    end
end
return true
"""

HMINCR = """
for _, key in ipairs(KEYS) do
    for i, v in ipairs(ARGV) do
        redis.call('HINCRBY', key, v, 1)
    end
end
return true
"""

HDIVH = """
for i, v in ipairs(ARGV) do
    local n = tonumber(redis.call('HGET', KEYS[2], v))
    local d = tonumber(redis.call('HGET', KEYS[3], v))
    if n and d then
        redis.call('HSET', KEYS[1], v, string.format(KEYS[4],n/d))
    end
end
return true
"""

HDIVK = """
local d = tonumber(redis.call('GET', KEYS[3]))
for i, v in ipairs(ARGV) do
    local n = tonumber(redis.call('HGET', KEYS[2], v))
    if n then
        redis.call('HSET', KEYS[1], v, string.format(KEYS[4],n/d))
    end
end
return true
"""

AVGRANGE = """
local start = tonumber(ARGV[1])
-- lua for loops are [start,stop]
local stop = tonumber(ARGV[2]) - 1
local n = 0
local sum = 0
for i=start,stop do
    local v = redis.call('HGET', KEYS[1], i)
    if v then
        sum = sum + tonumber(v)
        n = n + 1
    end
end

if n > 0 then
    return string.format('%.15g',sum/n)
else
    return nil
end
"""

SETAVGMAX = """
for crate=0,19 do
    local crate_n = 0
    local crate_sum = 0
    local crate_max = nil
    for card=0,15 do
        local card_n = 0
        local card_sum = 0
        local card_max = nil
        for channel=0,31 do
            local i = crate*512 + card*32 + channel
            local v = redis.call('HGET', KEYS[1], i)
            if v then
                v = tonumber(v)
                card_sum = card_sum + v
                card_n = card_n + 1

                if card_max == nil or v > card_max then
                    card_max = v
                end
            end
        end
        if card_n > 0 then
            redis.call('HSET', KEYS[4], crate*512 + card*32, card_sum/card_n)
            redis.call('HSET', KEYS[5], crate*512 + card*32, card_max)
        end

        crate_n = crate_n + card_n
        crate_sum = crate_sum + card_sum

        if card_max then
            if crate_max == nil or card_max > crate_max then
                crate_max = card_max
            end
        end
    end
    if crate_n > 0 then
        redis.call('HSET', KEYS[2], crate, crate_sum/crate_n)
        redis.call('HSET', KEYS[3], crate, crate_max)
    end
end
return true
"""

MAXRANGE = """
local start = tonumber(ARGV[1])
-- lua for loops are [start,stop]
local stop = tonumber(ARGV[2]) - 1
local max = nil
for i=start, stop do
    local v = redis.call('HGET', KEYS[1], i)
    if v then
        v = tonumber(v)

        if max == nil or v > max then
            max = v
        end
    end
end

if max == nil then
    return max
else
    return string.format('%.15g', max)
end
"""

_hmincrby = redis.register_script(HMINCRBY)
_setavgmax = redis.register_script(SETAVGMAX)
_hmincrbyfloat = redis.register_script(HMINCRBYFLOAT)
_hmincr = redis.register_script(HMINCR)
_hdivh = redis.register_script(HDIVH)
_hdivk = redis.register_script(HDIVK)
_avgrange = redis.register_script(AVGRANGE)
_maxrange = redis.register_script(MAXRANGE)

def setavgmax(key, client=None):
    """
    Sets the average and max values for crates in the hash key + ':crate:avg'
    and key + ':crate:max' respectively. Similarly for cards, where the card
    for a crate is indexed with the field crate*512 + card*32.
    """
    keys = [key, key + ':crate:avg', key + ':crate:max', key + ':card:avg', key + ':card:max']
    _setavgmax(keys=keys, args=[], client=client)
    return keys[1:]

def maxcard(key, crate, card, client=None):
    """
    Returns the maximum field value for channels in card `card`
    and crate `crate`.
    """
    start = (crate << 9) + (card << 5)
    stop = start + 32
    return _maxrange(keys=[key], args=[start,stop], client=client)

def maxcrate(key, crate, client=None):
    """Returns the maximum field value for channels in `crate`."""
    start = crate << 9
    stop = start + 16*32
    return _maxrange(keys=[key], args=[start,stop], client=client)

def avgcard(key, crate, card, client=None):
    """
    Returns the average field value for channels in card `card`
    and crate `crate`, not counting missing or 0 values.
    """
    start = (crate << 9) + (card << 5)
    stop = start + 32
    return _avgrange(keys=[key], args=[start,stop], client=client)

def avgcrate(key, crate, client=None):
    """
    Averages the hash fields for channels in a crate, not counting
    any missing or 0 values.

    Example:
        >>> redis.hmset('spam', {3584: 1, 3589: 100, 9728: 1e6})
        True
        >>> avgcrate('spam', 7)
        '50.5'
        >>> avgcrate('spam',19)
        '1e+06'
        >>> avgcrate('spam',0)
        None
    """
    start = crate << 9
    stop = start + 16*32
    return _avgrange(keys=[key], args=[start,stop], client=client)

def hmincrby(key, mapping, client=None):
    """
    Increment multiple fields in the hash stored at `key`.

    Example:
        >>> redis.hmset('spam', {'a': 0, 'b': 1})
        True
        >>> hmincrby('spam', {'a': 10, 'b': 1})
        1L
        >>> redis.hgetall('spam')
        {'a': '10', 'b': '2'}
    """
    args = chain.from_iterable(mapping.items())
    if isinstance(key, str):
        keys = [key]
    else:
        keys = key
    return _hmincrby(keys=keys, args=args, client=client)

def hmincrbyfloat(key, mapping, client=None):
    """
    Increment multiple fields in the hash stored at `key`.

    Example:
        >>> redis.hmset('spam', {'a': 0, 'b': 1})
        True
        >>> hmincrbyfloat('spam', {'a': 10, 'b': 1})
        1L
        >>> redis.hgetall('spam')
        {'a': '10.0', 'b': '2.0'}
    """
    args = chain.from_iterable(mapping.items())
    if isinstance(key, str):
        keys = [key]
    else:
        keys = key
    sargs = list(map(str, args))
#    print('k:', keys)
#    print('a:', sargs)
    return _hmincrbyfloat(keys=keys, args=sargs, client=client)

def hmincr(key, fields, client=None):
    """
    Increment multiple fields in the hash stored at `key` by 1.

    Example:
        >>> redis.hmset('spam', {'a': 0, 'b': 0})
        True
        >> hmincr('spam', ['a'])
        1L
        >>> redis.hgetall('spam')
        {'a': '1', 'b': '0'}
    """
    if isinstance(key, str):
        keys = [key]
    else:
        keys = key
    #print('k:', keys)
    #print('f:', list(map(str, fields)))
    return _hmincr(keys=keys, args=list(map(str, fields)), client=client)

def hdivh(result, a, b, fields, format='%.15g', client=None):
    """
    Divide multiple fields in the hash stored at `a` by
    fields in `b` and store the result in `result`.

    Example:
        >>> redis.hmset('a', {'a': 1, 'b': 2})
        True
        >>> redis.hmset('b', {'a': 2, 'b': 2})
        True
        >>> hdivh('c','a','b', ['a','b'])
        1L
        >>> redis.hgetall('c')
        {'a': '0.5', 'b': '1'}
    """
    return _hdivh(keys=[result,a,b,format], args=fields, client=client)

def hdivk(result, a, b, fields, format='%.15g', client=None):
    """
    Divide multiple fields in the hash stored at `a` by
    the value in key `b` and store the result in `result`.

    Example:
        >>> redis.hmset('a', {'a': 1, 'b': 2})
        True
        >>> redis.set('b', '2')
        True
        >>> hdivk('c','a','b', ['a','b'])
        1L
        >>> redis.hgetall('c')
        {'a': '0.5', 'b': '1'}
    """
    return _hdivk(keys=[result,a,b,format], args=fields, client=client)
