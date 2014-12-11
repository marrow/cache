# encoding: utf-8

from __future__ import unicode_literals

from mongoengine import Document, EmbeddedDocument
from mongoengine import StringField, DateTimeField, GenericReferenceField, DynamicField, EmbeddedDocumentField

from .exc import CacheMiss
from .compat import py3, unicode, iteritems
from .util import sha256, timedelta, resolve, wraps, ref, utcnow, chain, isclass, deque, contextmanager, stack, pformat


class CacheKey(EmbeddedDocument):
	prefix = StringField(db_field='p', default=None)
	reference = GenericReferenceField(db_field='r', default=None)
	hash = StringField(db_field='h')
	
	def __repr__(self):
		return "CacheKey({0.prefix}, {0.reference}, {0.hash})".format(self)


class Cache(Document):
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
	def memoize(cls, prefix=None, reference=None, expires=utcnow, weeks=0, days=0, hours=0, minutes=0, seconds=0, refresh=False, populate=True):
		""""""
		
		def generate_expiry():
			if weeks or days or hours or minutes or seconds:
				return expires() + timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
			
			return (expires() + cls.DEFAULT_DELTA) if cls.DEFAULT_DELTA else expires()
		
		def decorator(fn):
			pfx = resolve(fn) if prefix is None else prefix
			
			@wraps(fn)
			def inner(*args, **kw):
				key = CacheKey(prefix=pfx, reference=reference, hash=cls.keyfunc(args, kw))
				
				try:
					return cls.get(key, refresh=generate_expiry if refresh else None)
				except CacheMiss:
					if not populate:
						raise
				
				return cls.set(key, fn(*args, **kw), generate_expiry()).value
			
			# TODO: inner.cache QuerySet descriptor
			inner.wraps = ref(fn)  # Don't want circular references, now.
			
			return inner
		
		return decorator
	
	@classmethod
	def method(cls, *attributes, **innerkwargs):
		""""""
		
		def decorator(fn):
			prefix = innerkwargs.pop('prefix', None)
			if not prefix: prefix = resolve(fn)
			
			@wraps(fn)
			def inner(self, *args, **kw):
				if 'reference' not in innerkwargs and isinstance(self, Document):
					veto = getattr(self, '__nocache__', False)
					
					if not self.pk or self._created or (veto and veto[-1]):
						return fn(self, *args, **kw)  # Can't safely cache.
					
					innerkwargs['reference'] = self.pk
				
				# This combines the fields we pull and the reference default by nesting a call to memoize.
				@cls.memoize(prefix, **innerkwargs)  # Dogfood, yum!
				def xyzzy(*magic):
					return fn(self, *args, **kw)
				
				# This is excessively ugly, but works.
				# It prefixes the expected arglist with the dependent values.
				return xyzzy(*chain((fetch(self, i) for i in attributes), args))
			
			return inner
		
		return decorator
	
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
	
	# ### Utility Methods
	
	@staticmethod
	def keyfunc(args, kw):
		key = sha256()
		key.update(unicode(pformat(args)).encode('utf8'))
		key.update(unicode(pformat(kw)).encode('utf8'))
		return key.hexdigest()
