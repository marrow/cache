# encoding: utf-8

# # Imports

from __future__ import unicode_literals

from mongoengine import Document, EmbeddedDocument
from mongoengine import StringField, DateTimeField, GenericReferenceField, DynamicField, EmbeddedDocumentField

from .exc import CacheMiss
from .compat import py3, unicode, iteritems
from .util import sha256, timedelta, resolve, wraps, ref, utcnow, chain, isclass, deque, contextmanager, stack, pformat, fetch


# # Implementation

# ## Utility Classes

class CacheKey(EmbeddedDocument):
	"""The unique key cached values are indexed on."""
	
	prefix = StringField(db_field='p', default=None)
	reference = GenericReferenceField(db_field='r', default=None)
	hash = StringField(db_field='h')
	
	def __repr__(self):
		return "CacheKey({0.prefix}, {0.reference}, {0.hash})".format(self)
	
	def __str__(self):
		return repr(self)
	
	@classmethod
	def new(cls, prefix, reference, args, kw):
		hash = sha256()
		print("hashing", unicode(pformat(args)).encode('utf8'))
		print("hashing", unicode(pformat(kw)).encode('utf8'))
		hash.update(unicode(pformat(args)).encode('utf8'))
		hash.update(unicode(pformat(kw)).encode('utf8'))
		
		result = cls(prefix=prefix, reference=reference, hash=hash.hexdigest())
		print("> result", result)
		return result


class CacheMark(object):
	def __init__(self, manager, expiry, prefix=None, reference=False, refresh=False, populate=True, processor=None):
		self.manager = manager
		self.expiry = expiry
		self.prefix = prefix
		self.reference = reference
		self.refresh = refresh
		self.populate = populate
		self.processor = processor
		
		super(CacheMark, self).__init__()
	
	def __call__(self, fn):
		@wraps(fn)
		def cache_mark_inner(*args, **kw):
			print(self.__dict__, self.expiry())
			
			prefix = self.prefix
			if not prefix:
				prefix = resolve(fn)
				print('calculated prefix:', prefix)
			
			reference = self.reference
			if reference and args and isinstance(args[0], Document):
				print("ref", reference, args[0])
				veto = getattr(args[0], '__nocache__', False)
				
				if not args[0].pk or args[0]._created or (veto and veto[-1]):
					print("VETO")
					return fn(*args, **kw)  # Can't safely cache.
				
				reference = self.pk if reference is True else reference
			
			_args = self.processor(args, kw) if self.processor else (args, kw)
			print("<<<", _args, self.processor)
			key = CacheKey.new(prefix, None if reference is True or reference is False else reference, *_args)
			
			try:
				return self.manager.get(key, refresh=self.expiry if self.refresh else None)
			except CacheMiss:
				if not self.populate:
					raise
				
			return self.manager.set(key, fn(*args, **kw), self.expiry()).value
		
		cache_mark_inner.__func__ = fn
		
		return cache_mark_inner


# ## Primary Class

class Cache(Document):
	"""A cached value."""
	
	meta = dict(
			collection = "cache",
			allow_inheritance = False,
			indexes = [
					dict(fields=('expires', ), expireAfterSeconds=0)
				]
		)
	
	# ### Constants
	
	DEFAULT_DELTA = timedelta(weeks=1, days=0, hours=0, minutes=0, seconds=0)
	
	# ### Fields
	
	key = EmbeddedDocumentField(CacheKey, db_field='_id', primary_key=True)
	value = DynamicField(db_field='v')
	expires = DateTimeField(db_field='e', default=lambda: utcnow() + timedelta(weeks=1))
	
	# ### Magic Methods
	
	def __repr__(self):
		return 'Cache({1.prefix}, {1.reference}, {1.hash}, {0.expires})'.format(self, self.key if self.key else CacheKey())
	
	# ### Basic Accessors
	
	@classmethod
	def get(cls, criteria, refresh=None):
		""""""
		
		# TODO: Upserts, baby!  Benchmark first, of course.
		# TODO: deque enable/disable context manager glue
		
		result = cls.objects(pk=criteria).scalar('expires', 'value').first()
		
		if not result:
			raise CacheMiss()
		
		if result[0] <= utcnow():
			cls.objects(pk=criteria).delete()
			raise CacheMiss()
		
		if refresh:
			cls.objects(pk=criteria).update(set__expires=refresh(), write_concern={'w': 0})
		
		return result[1]
	
	@classmethod
	def set(cls, criteria, value, expires):
		""""""
		
		# TODO: Pipe out to SON and back to ensure consistent return types.
		return cls(pk=criteria, value=value, expires=expires).save(force_insert=True, write_concern={'w': 0})
	
	# ### Decorators
	
	@classmethod
	def generate_expiry(cls, expires, weeks, days, hours, minutes, seconds):
		def generate_expiry_inner():
			if weeks or days or hours or minutes or seconds:
				return expires() + timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
			
			return (expires() + cls.DEFAULT_DELTA) if cls.DEFAULT_DELTA else expires()
		
		return generate_expiry_inner
	
	@classmethod
	def memoize(cls, prefix=None, reference=None, expires=utcnow, weeks=0, days=0, hours=0, minutes=0, seconds=0, refresh=False, populate=True):
		""""""
		
		return CacheMark(
				cls,
				cls.generate_expiry(expires, weeks, days, hours, minutes, seconds),
				prefix,
				False if reference is None else reference,
				refresh,
				populate
			)
	
	@classmethod
	def method(cls, *attributes, **kw):
		""""""
		def method_args_callback(args, kw):
			print("fetching on", attributes)
			for i in attributes:
				print("calc", i, args[0], fetch(args[0], i))
			print("returning", (tuple(fetch(args[0], i) for i in attributes) + args[1:]), kw)
			return (tuple(fetch(args[0], i) for i in attributes) + args[1:]), kw
		
		return CacheMark(
				cls,
				cls.generate_expiry(kw.pop('expires', utcnow),
					**dict((i, kw.get(i, 0)) for i in ('weeks', 'days', 'hours', 'minutes', 'seconds'))),
				kw.get('prefix', None),
				kw.get('reference', True),
				kw.get('refresh', False),
				kw.get('populate', True),
				method_args_callback
			)
	
	# ### Context Managers
	
	@staticmethod
	@contextmanager
	def disable(target=None):
		with stack(Document if target is None else target, '__nocache__', True):
			yield
	
	@staticmethod
	@contextmanager
	def enable(target=None):
		with stack(Document if target is None else target, '__nocache__', False):
			yield
