# encoding: utf-8

import os
import sys
import math
import pytest

from itertools import chain
from inspect import isfunction, ismethod, isclass
from textwrap import TextWrapper

from marrow.cache.compat import py3
from marrow.cache.util import *


canaried = pytest.mark.skipif(bool(os.environ.get('CANARY', False)), reason="No im_class or __qualname__ support.")
requires_qualname = pytest.mark.skipif(sys.version_info < (3, 3), reason="Use requires __qualname__ support.")


def bare():
	pass


class Example(object):
	def instance(self):
		return self
	
	@classmethod
	def classmethod(cls):
		return cls
	
	@staticmethod
	def staticmethod():
		pass



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


class TestResolve(object):
	def test_bare(self):
		assert resolve(bare) == 'test.test_util:bare'
	
	def test_class(self):
		assert resolve(Example) == 'test.test_util:Example'
	
	def test_class_instance(self):
		assert resolve(Example()) == 'test.test_util:Example'
	
	@canaried
	def test_instance(self):
		assert resolve(Example.instance) == 'test.test_util:Example.instance'
		assert resolve(Example().instance) == 'test.test_util:Example.instance'
	
	@canaried
	def test_classmethod(self):
		assert resolve(Example.classmethod) == 'test.test_util:Example.classmethod'
		assert resolve(Example().classmethod) == 'test.test_util:Example.classmethod'
	
	@requires_qualname
	def test_static(self):
		assert resolve(Example.staticmethod) == 'test.test_util:Example.staticmethod'
		assert resolve(Example().staticmethod) == 'test.test_util:Example.staticmethod'
