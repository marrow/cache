# encoding: utf-8

from pytest import yield_fixture
from unittest import TestCase

from marrow.cache.exc import CacheMiss
from marrow.cache.model import CacheKey, Cache
from marrow.cache.util import utcnow, timedelta, contextmanager


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


def new_ck():
	return CacheKey.new('test', None, tuple(), dict())


@contextmanager
def saved_cv():
	record = Cache(key=new_ck(), value='value', expires=None)
	record.expires = utcnow() + Cache.DEFAULT_DELTA
	yield record.save()
	record.delete()


@contextmanager
def acfunc(**kw):
	@Cache.memoize(prefix='acfunc', **kw)
	def inner():
		inner.called = True
		return 27  # [Someone's favourite number. @amcgregor -ed]
	
	inner.called = False
	
	try:
		yield inner
	except:
		pass
	
	Cache.objects(key__prefix='acfunc').delete()


@Cache.memoize()
def bare():
	return "Hello world!"


class TestCacheKey(TestCase):
	ck = new_ck()
	
	def test_basic_attribute_behaviour(self):
		assert self.ck.prefix == 'test'
		assert self.ck.reference is None
		assert self.ck.hash == NO_ARGUMENTS
	
	def test_programmers_representation(self):
		rep = repr(self.ck)
		
		assert 'test' in rep
		assert 'None' in rep
		assert NO_ARGUMENTS in rep


class TestCacheGeneral(TestCase):
	def test_programmers_representation(self):
		rep = repr(Cache(key=new_ck(), value='value', expires=None))
		assert 'test' in rep
		assert 'None' in rep
		assert NO_ARGUMENTS in rep
	
	def test_explicit_cache_assignment(self):
		record = Cache.set(new_ck(), 27, utcnow() + Cache.DEFAULT_DELTA)
		assert record.pk
		assert not record._created
		assert record.value == 27
	
	def test_explicit_retrieval_ofS_an_extant_key(self):
		with saved_cv() as cv:
			assert Cache.get(cv.key) == 'value'
	
	def test_explicit_retrieval_of_a_missing_key(self):
		try:
			Cache.get(new_ck())
		except CacheMiss:
			pass
		else:
			assert False, "Failed to raise CacheMiss."
	
	def test_retrieval_of_expired_values(self):
		Cache.drop_collection()
		
		# We don't recreate the indexes yet because we want the record to survive long enough to test.
		
		new_cv = Cache(key=new_ck(), value='value', expires=None)
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
	
	def test_refreshing_on_cache_hit(self):
		with saved_cv() as cv:
			Cache.get(cv.key, refresh=lambda: utcnow() + Cache.DEFAULT_DELTA)
			assert cv.expires < cv.reload().expires


class TestCacheMemoize(TestCase):
	def test_automatic_prefixes(self):
		assert Cache.objects.count() == 0
		
		assert bare() == "Hello world!"
		
		assert Cache.objects.count() == 1
		
		co = Cache.objects.first()
		
		assert co.key.prefix == 'test.test_model:bare'
		assert co.value == "Hello world!"
		
		Cache.objects.delete()
	
	def test_validate_default_behaviour(self):
		with acfunc() as fn:
			assert fn() == 27
			assert fn.called == True
			
			fn.called = False
			assert fn() == 27
			assert fn.called == False
			
			assert Cache.objects.count() == 1
			
			expires = Cache.objects.scalar('expires').first()
			delta = (expires - utcnow()) + timedelta(seconds=10)  # Fude-factor.
			
			assert delta.days == 7
	
	def test_validate_custom_expiry_delta(self):
		with acfunc(minutes=5) as inner:
			assert inner() == 27
			
			expires = Cache.objects.scalar('expires').first()
			delta = (expires - utcnow()) + timedelta(seconds=10)  # Fude-factor.
			
			assert (5*60) < delta.seconds < (5.25*60)
		
	def test_ensure__populate_false__does_not_populate(self):
		with acfunc(populate=False) as inner:
			try:
				inner()
			except CacheMiss:
				pass
			else:
				assert False, "Failed to raise CacheMiss."
			
			assert Cache.objects.count() == 0


class Example(object):
	example = dict(somevalue=27)
	
	@property
	@Cache.method(prefix='Example.sample')
	def sample(self):
		return self.example
	
	@Cache.method('number', prefix='Example.sample_number')
	def sample_number(self):
		return self.number * 2
	
	@Cache.method('sample.somevalue', prefix='Example.sample_somevalue')
	def sample_somevalue(self):
		return self.example['somevalue'] * 4


class TestCacheMethod(TestCase):
	def test_instance_property(self):
		# [IMPORTANT NOTE WARNING WARNING DANGER WILL ROBINSON YOU FEEL DREAD -ed]
		#  Default .method() usage without dependent values declared effectively ignores that it might be an instance.
		#  Ensure you pass arguments to the method to key it on something, or pass in an explicit prefix+reference when
		#  used as a closure.
		# TODO: #1 Yes, this is buried in the tests for now. @amcgregor #yolo -ed
		
		instance = Example()
		
		assert instance.sample == dict(somevalue=27)
		assert Cache.objects.count() == 1
		
		co = Cache.objects.first()
		
		assert co.key.hash == NO_ARGUMENTS
		
		co.delete()  # Clean up.
	
	def test_dependent_instance_method(self):
		instance = Example()
		instance.number = 4
		assert instance.sample_number() == 8
		assert Cache.objects.count() == 1
		
		instance.number = 8
		assert instance.sample_number() == 16
		assert Cache.objects.count() == 2
		
		Cache.objects.delete()
	
	def test_recursive_dependence(self):
		instance = Example()
		assert instance.sample_somevalue() == 108
		assert Cache.objects.count() == 2, Cache.objects()
		
		instance.example = dict(somevalue=42)
		assert instance.sample_somevalue() == 108
		assert Cache.objects.count() == 2
		
		Cache.objects.delete()
