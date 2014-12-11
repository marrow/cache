# encoding: utf-8

from pytest import yield_fixture

from marrow.cache.model import *


@yield_fixture(scope="module", autouse=True)
def connection(request):
	"""These are live tests, so we need an active connection.
	
	It's also nice to clean up after yourself.
	"""
	
	from mongoengine import connect
	
	connect('test')
	
	Cache.drop_collection()
	Cache.ensure_indexes()
	
	yield
	
	Cache.drop_collection()


class TestCacheKey(object):
	def test_new(self):
		ck = CacheKey.new('foo', None, tuple(), dict())
		assert ck.prefix == 'foo'
		assert ck.reference is None
		assert ck.hash == '4f888e090430fea81ed3e2f31a2824445a98e2877f0048502d57d8ead350cb5b'
