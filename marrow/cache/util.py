# encoding: utf-8

"""Convienent utilities."""

from __future__ import print_function

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

from .compat import iteritems


# ## Weird Aliases

utcnow = datetime.utcnow


# ## Class Definitions




# ## Function Definitions

'''
def resolve(obj):
	"""This helper function attempts to resolve the dot-colon import path for the given object.
	
	This is the inverse of 'lookup', which will turn the dot-colon path back into the object.
	
	Python 3.3 added a substantially improved way of determining the fully qualified name for objects;
	this updated method will be used if available.  Note that running earlier versions will prevent correct
	association of nested objects (i.e. objects not at the top level of a module).
	"""
	
	finalize = lambda r: getmodule(obj).__name__ + ':' + r
	
	#if not hasattr(obj, '__name__') and hasattr(obj, '__class__'):
	#	obj = obj.__class__
	
	try:  # Python 3.3+, this short-cut saves a lot of work.  Pypy3 will elide this entire function away.
		return finalize(obj.__qualname__)
	except AttributeError:
		pass
	
	oobj = obj
	if not hasattr(obj, '__name__'):  # Handles resolution of a pure instance to its class.
		obj = obj.__class__
	
	name = obj.__name__
	
	# Handle the quick case, where the referenced value is a top-level object of its module.
	if getattr(getmodule(obj), name, None):
		return finalize(name)
	
	elif isclass(obj):  # Canary died.
		raise TypeError("Can't determine canonical name of: " + repr(obj))
	
	# im_self handles (un)bound classmethods, im_class handles (un)bound instancemethods
	# NOTE: But only if evaluated in this order!
	for candidate in (getattr(obj, i) for i in ('im_self', 'im_class', '__self__') if hasattr(obj, i)):
		if not isclass(candidate):
			continue
		
		return finalize(candidate.__name__ + '.' + name)
	
	# We didn't find a worthy candidate, so searching now gets hard.
	# Look through the module for any top-level objects that have this one as an attribute.
	
	for parent, candidate in iteritems(getmodule(obj).__dict__):
		if parent.startswith('_'): continue  # As a safety measure, we don't inspect pseudo-private attributes.
		
		print("Looking for", name, "on", repr(candidate), "a module attribute named", parent)
		print("<<<", getattr(candidate, name, None), obj, id(getattr(candidate, name, None)), id(obj))
		
		try:
			if candidate.__dict__.get(name, None) == obj:
				print("!!! Found.")
				return finalize(parent + '.' + name)
		except AttributeError:
			pass
	
	print("???", name, getmodule(obj).__name__, repr(obj), dir(obj))
	print(">>>", getattr(obj, '__self__', None))
	print(">>>", getattr(obj, 'im_self', None))
	
	# Well, not much left to do but explode.
	raise TypeError("Can't determine canonical name of: " + repr(obj))
'''

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

