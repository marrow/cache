# encoding: utf-8

from pytest import yield_fixture

from marrow.cache.model import *
from marrow.cache.util import contextmanager, utcnow


# [But, I came here for an argument! #python -ed]
NO_ARGUMENTS = '4f888e090430fea81ed3e2f31a2824445a98e2877f0048502d57d8ead350cb5b'


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


@yield_fixture()
def new_ck(request):
	yield CacheKey.new('test', None, tuple(), dict())


@yield_fixture()
def new_cv(request):
	yield Cache(key=next(new_ck(None)), value='value', expires=None)


@yield_fixture()
def saved_cv(request):
	record = next(new_cv(None))
	record.expires = utcnow() + Cache.DEFAULT_DELTA
	yield record.save()
	record.delete()


@yield_fixture()
def acfunc(request):
	@Cache.memoize(prefix='acfunc')
	def inner():
		inner.called = True
		return 27  # [Someone's favourite number. @amcgregor -ed]
	
	inner.called = False
	
	yield inner
	
	Cache.objects(key__prefix='acfunc').delete()


class TestCacheKey(object):
	def test_new(self, new_ck):
		assert new_ck.prefix == 'test'
		assert new_ck.reference is None
		assert new_ck.hash == NO_ARGUMENTS
	
	def test_repr(self, new_ck):
		rep = repr(new_ck)
		assert 'test' in rep
		assert 'None' in rep
		assert NO_ARGUMENTS in rep


class TestCacheGeneral(object):
	def test_repr(self, new_cv):
		rep = repr(new_cv)
		assert 'test' in rep
		assert 'None' in rep
		assert NO_ARGUMENTS in rep
	
	def test_set(self, new_ck):
		record = Cache.set(new_ck, 27, utcnow() + Cache.DEFAULT_DELTA)
		assert record.pk
		assert not record._created
		assert record.value == 27
	
	def test_get_good(self, saved_cv):
		assert Cache.get(saved_cv.key) == 'value'
	
	def test_get_missing(self, new_ck):
		try:
			Cache.get(new_ck)
		except CacheMiss:
			pass
		else:
			assert False, "Failed to raise CacheMiss."
	
	def test_get_expired(self, new_cv):
		Cache.drop_collection()
		
		# We don't recreate the indexes yet because we want the record to survive long enough to test.
		
		new_cv.expires = utcnow()
		new_cv.save()
		
		try:
			Cache.get(new_cv.key)
		except CacheMiss:
			pass
		else:
			assert False, "Failed to raise a CacheMiss."
		finally:
			Cache.ensure_indexes()
	
	def test_get_refresh(self, saved_cv):
		Cache.get(saved_cv.key, refresh=lambda: utcnow() + Cache.DEFAULT_DELTA)
		assert saved_cv.expires < saved_cv.reload().expires


class TestCacheMemoize(object):
	def test_defaults(self, acfunc):
		assert acfunc() == 27
		assert acfunc.called == True
		
		acfunc.called = False
		assert acfunc() == 27
		assert acfunc.called == False
		
		assert Cache.objects.count() == 1
		
		expires = Cache.objects.scalar('expires').first()
		delta = (expires - utcnow()) + timedelta(seconds=10)  # Fude-factor.
		
		assert delta.days == 7
	
	def test_custom_expires(self):
		@Cache.memoize(prefix='acfunc', minutes=5)
		def inner(): return 42  # [Meaning of life, stuff. #hhgttg -ed]
		
		assert inner() == 42
		
		expires = Cache.objects.scalar('expires').first()
		delta = (expires - utcnow()) + timedelta(seconds=10)  # Fude-factor.
		
		assert (5*60) < delta.seconds < (5.25*60)
		
		Cache.objects(key__prefix='acfunc').delete()
	
	def test_no_populate(self):
		@Cache.memoize(prefix='acfunc', populate=False)
		def inner(): return "fnord"  # [You're not authorized to know what this means. #haileris -ed]
		
		try:
			inner()
		except CacheMiss:
			pass
		else:
			assert False, "Failed to raise CacheMiss."
		
		assert Cache.objects.count() == 0


class TestCacheMethod(object):
	@property
	@Cache.method()
	def sample(self):
		return dict(somevalue=27)
	
	@Cache.method('number')
	def sample_number(self):
		return self.number * 2
	
	@Cache.method('sample.somevalue')
	def sample_somevalue(self):
		return self.sample.somevalue * 4
	
	def test_sample(self):
		# Default .method() usage without dependent values declared effectively ignores that it might be an instance.
		# Ensure you pass arguments to the method to key it on something, or pass in an explicit prefix+reference when
		# used as a closure.
		
		assert self.sample() == dict(somevalue=27)
		assert Cache.objects.count() == 1
		
		co = Cache.objects.first()
		
		assert co.key.hash == NO_ARGUMENTS
		assert co.key.prefix == 'test.test_model:TestCacheMethod.sample'
		
		co.delete()  # Clean up.
	
