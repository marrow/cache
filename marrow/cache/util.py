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

from .compat import iteritems, py2


# ## Weird Aliases

utcnow = datetime.utcnow


# ## Function Definitions

def resolve(obj):
	"""Attempt to resolve an object reference to its fully qualified name.
	
	There are strong caveats to the use of this function:
	
	* It operates best on Python 3.3+ compatible interpreters due to the presence of ``__qualname__``. All features
	  are fully supported.
	
	* Under other versions:
	
		* Functions declared ``@staticmethod`` cannot be referenced; doing so will produce _erroneous results_.  The
		  only "bare functions" resolved should be at the module scope.
		
		* This function can not be used to reference closures.
		
	* Under Python 3, prior to 3.3 and including current versions of Pypy3, class methods, static methods, and
	  instance methods can not be referenced. This is due to dropping Python 2-style ``im_class``, and ``im_self``
	  attributes—used for discovery and formerly provided by a data descriptor that wraps the actual function—without
	 ``__qualname__`` to replace it.
	"""
	
	finalize = lambda r: getmodule(obj).__name__ + ':' + r
	
	try:
		return finalize(obj.__qualname__)
	except AttributeError:
		pass
	
	if isfunction(obj) and not ismethod(obj):  # pragma: no cover - tested under py2
		return finalize(obj.__name__)
		
	if not isclass(obj) and hasattr(obj, '__class__') and not hasattr(obj, 'im_class'):
		obj = obj.__class__
	
	if isclass(obj):
		if obj not in getmodule(obj).__dict__.values():
			raise TypeError("Can't determine canonical name of: " + repr(obj))
		
		return finalize(obj.__name__)
	
	if hasattr(obj, 'im_self') and obj.im_class:  # pragma: no cover - tested under py2, irrelevant on py3
		if obj.im_self:
			if isclass(obj.im_self):
				return finalize(obj.im_self.__name__ + '.' + obj.__name__)
			
			return finalize(obj.im_self.__class__.__name__ + '.' + obj.__name__)
		
		return finalize(obj.im_class.__name__ + '.' + obj.__name__)


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

