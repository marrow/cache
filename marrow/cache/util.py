# encoding: utf-8

"""Convienent utilities."""

# ## Imports

from warnings import warn
from weakref import ref
from functools import wraps
from itertools import chain
from inspect import getmodule, isclass
from collections import deque
from contextlib import contextmanager
from hashlib import sha256
from datetime import datetime, timedelta
from pprint import pformat


# ## Weird Aliases

utcnow = datetime.utcnow


# ## Class Definitions




# ## Function Definitions

def resolve(obj):
	"""This helper function attempts to resolve the dot-colon import path for the given object.
	
	This is the inverse of 'lookup', which will turn the dot-colon path back into the object.
	
	Python 3.3 added a substantially improved way of determining the fully qualified name for objects;
	this updated method will be used if available.  Note that running earlier versions will prevent correct
	association of nested objects (i.e. objects not at the top level of a module).
	"""
	
	if not hasattr(obj, '__name__') and hasattr(obj, '__class__'):
		obj = obj.__class__
	
	q = getattr(obj, '__qualname__', None)
	
	if not q:
		q = obj.__name__
		
		if hasattr(obj, 'im_class'):
			q = obj.im_class.__name__ + '.' + q
	
	return getmodule(obj).__name__ + ':' + q


def fetch(obj, reference, default=None):
	value = obj
	separator = True
	remainder = reference
	
	while separator:
		name, separator, remainder = remainder.partition('.')
		numeric = name.lstrip('-').isnumeric()
		
		try:
			if numeric: raise AttributeError()
			value = getattr(value, name)
		except AttributeError:
			try:
				value = value[int(name) if numeric else name]
			except (KeyError, TypeError):
				if default:
					return default
				
				raise
	
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

