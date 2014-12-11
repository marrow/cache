# encoding: utf-8

import os
import sys
import pytest

from inspect import isfunction, ismethod, isclass

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
