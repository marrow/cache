# encoding: utf-8

"""A classic fibonacci solver example.

With MongoDB on the same host, this script should exhibit a ~2:1 speed-up.

Example output of ``time python basic.py``::

	Connecting...
	Preparing...
	Cache Bypass: 100 loops, best of 3: 2.12 msec per loop
	Cached: 1000 loops, best of 3: 1.07 msec per loop
	Cached w/ Refresh: 1000 loops, best of 3: 1.43 msec per loop
	The 50th fibonacci number is: 12586269025 or 12586269025
	Total cached objects: 51
	
	Recorded prefixes: __main__:fibonacci
	
	Example cache key:
	CacheKey(__main__:fibonacci, None, 92f4d3af051f64c9f17c61626606088937521b4c4b0606d72dddddc474bbcb8f)
	
	Cleaning up...
	python basic.py  10.57s user 0.40s system 91% cpu 11.933 total

"""


from __future__ import unicode_literals, print_function

from timeit import main as timeit
from mongoengine import connect

from marrow.cache import Cache

flush = __import__('sys').stdout.flush


@Cache.memoize(minutes=5)
def fibonacci(n):
	if n == 0:
		return 0
	
	elif n == 1:
		return 1
	
	return fibonacci(n-1) + fibonacci(n-2)


fib_refresh = Cache.memoize(minutes=5, refresh=True)(fibonacci.wraps())


if __name__ == '__main__':
	# First, open a database connection.
	print("Connecting...")
	connect('test')
	
	# Then, since this is likely the first time running, we'll ensure the indexes exist, and no data does.
	print("Preparing...")
	Cache.drop_collection()
	Cache.ensure_indexes()
	
	# First, the unoptimized approach.
	print("Cache Bypass: ", end=''); flush()
	timeit(('-s', 'from __main__ import fibonacci', 'fibonacci.wraps()(50)'))
	
	# Now, what happens when we use the cache?
	print("Cached: ", end=''); flush()
	timeit(('-s', 'from __main__ import fibonacci', 'fibonacci(50)'))
	
	# Lastly, what happens when we use the cache and allow it to update itself?
	print("Cached w/ Refresh: ", end=''); flush()
	timeit(('-s', 'from __main__ import fib_refresh', 'fib_refresh(50)'))
	
	print("The 50th fibonacci number is:", fibonacci(50), "or", fibonacci.wraps()(50))
	
	# Emit some interesting statistics:
	print("Total cached objects:", Cache.objects.count())
	print("\nRecorded prefixes:", ", ".join(j for j in set(i.key.prefix for i in Cache.objects.only('key'))))
	
	print("\nExample cache key:\n", repr(Cache.objects.scalar('key').first()), sep='')
	
	# We now clean up after ourselves.
	print("\nCleaning up...")
	Cache.drop_collection()
