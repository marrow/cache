# encoding: utf-8

"""Convienent utilities."""

from __future__ import print_function

# ## Imports

from warnings import warn
from weakref import ref
from functools import wraps
from itertools import chain
from inspect import getmodule, isclass, isfunction, ismethod
from collections import deque
from contextlib import contextmanager
from hashlib import sha256
from datetime import datetime, timedelta
from pprint import pformat

from .compat import iteritems


# ## Weird Aliases

utcnow = datetime.utcnow


# ## Class Definitions




# ## Function Definitions


def resolve(obj):
	finalize = lambda r: getmodule(obj).__name__ + ':' + r
	
	def search():
		space = getmodule(obj).__dict__
		for key in space:
			if key.startswith('_') or not isclass(space[key]) or obj.__name__ not in space[key].__dict__:
				continue
			
			if space[key].__dict__[obj.__name__] is not obj:
				continue
				
			return finalize(key + '.' + obj.__name__)
		
		raise TypeError("Can't determine canonical name of: " + repr(obj))
	
	try:
		return finalize(obj.__qualname__)
	except AttributeError:
		pass
	
	if isfunction(obj) and not ismethod(obj):
		if getmodule(obj).__dict__.get(obj.__name__, None):
			return finalize(obj.__name__)
		
		return search()
	
	if not isclass(obj) and hasattr(obj, '__class__') and not hasattr(obj, 'im_class'):
		obj = obj.__class__
	
	if isclass(obj):
		if obj not in getmodule(obj).__dict__.values():
			raise TypeError("Can't determine canonical name of: " + repr(obj))
		
		return finalize(obj.__name__)
	
	if hasattr(obj, 'im_self') and obj.im_class:
		if obj.im_self:
			if isclass(obj.im_self):
				return finalize(obj.im_self.__name__ + '.' + obj.__name__)
			
			return finalize(obj.im_self.__class__.__name__ + '.' + obj.__name__)
		
		return finalize(obj.im_class.__name__ + '.' + obj.__name__)
		
		return search()


def fetch(obj, reference, default=None):
	value = obj
	separator = True
	remainder = reference
	
	while separator:
		name, separator, remainder = remainder.partition('.')
		numeric = name.lstrip('-').isdigit()
		
		try:
			if numeric: raise AttributeError()
			value = getattr(value, name)
		except AttributeError:
			try:
				value = value[int(name) if numeric else name]
			except (KeyError, TypeError):
				return default
	
	return value


# ### Context Managers

@contextmanager
def stack(target, attribute, value):
	# Allow multiple nested invocations; they're a stack.
	container = getattr(target, attribute, None)
	
	if container is None:
		container = deque()
		setattr(target, attribute, container)
	
	container.append(value)
	
	yield
	
	container.pop()
	
	if not container:
		delattr(target, attribute)

