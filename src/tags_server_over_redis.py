#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pottery
from redis import redis
from redis import redis
import redis
from redis import redis
from redis import Redis
redis = Redis.from_url('http://localhost:6379/')
from pottery import RedisDict
raj = RedisDict(redis=redis, key='raj')
a = RedisList(redis=redis, key='raj')
from pottery import *
a = RedisList(redis=redis, key='raj')
a.count()
a.count(1)
a.append(0)
a.append(['abc'])
a.append(['abc', 1])
a.append(['abc', 1, {1:[2]}])
a.append(['abc', 1, {1:[2, a]}])



"""
https://redisdesktop.com/subscribe
https://github.com/uglide/qredisclient
https://github.com/RedisLabsModules/RediSearch


"""