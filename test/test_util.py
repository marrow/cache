# encoding: utf-8

import os
import sys
import pytest

from unittest import TestCase

from marrow.cache.util import resolve


canaried = pytest.mark.skipif(bool(os.environ.get('CANARY', False)), reason="No im_class or __qualname__ support.")
not_canaried = pytest.mark.skipif(not bool(os.environ.get('CANARY', False)), reason="im_class or __qualname__ support required.")
requires_qualname = pytest.mark.skipif(sys.version_info < (3, 3), reason="Use requires __qualname__ support.")
not_requires_qualname = pytest.mark.skipif(sys.version_info >= (3, 3), reason="Use requires __qualname__ support to be missing.")


def bare():
	pass


class Example(object):
	class Pandora(object):
		pass
	
	def instance(self):
		return self
	
	@classmethod
	def classmethod(cls):
		return cls
	
	@staticmethod
	def staticmethod():
		pass



class TestResolver(TestCase):
	def test__resolve__of_a_module_level_function(self):
		assert resolve(bare) == 'test.test_util:bare'
	
	def test__resolve__of_a_module_level_class(self):
		assert resolve(Example) == 'test.test_util:Example'
	
	def test__resolve__of_a_module_level_class_instance(self):
		assert resolve(Example()) == 'test.test_util:Example'
	
	@canaried
	def test__resolve__of_an_instance_method(self):
		assert resolve(Example.instance) == 'test.test_util:Example.instance'
		assert resolve(Example().instance) == 'test.test_util:Example.instance'
	
	@canaried
	def test__resolve__of_a_class_method(self):
		assert resolve(Example.classmethod) == 'test.test_util:Example.classmethod'
		assert resolve(Example().classmethod) == 'test.test_util:Example.classmethod'
	
	def test_resolve_failures(self):
		def inner(obj):
			try:
				assert resolve(obj)
			except TypeError:
				pass
			else:
				assert False, "Failed to raise TypeError."
		
		for i in (Example.instance, Example.classmethod):
			yield not_canaried(inner), i
		
		yield not_requires_qualname(inner), Example.staticmethod
	
	@requires_qualname
	def test__resolve__of_a_static_method(self):
		assert resolve(Example.staticmethod) == 'test.test_util:Example.staticmethod'
		assert resolve(Example().staticmethod) == 'test.test_util:Example.staticmethod'
