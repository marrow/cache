# encoding: utf-8

import os
import sys
import pytest

from unittest import TestCase

from marrow.cache.util import resolve


canaried = pytest.mark.skipif(bool(os.environ.get('CANARY', False)), reason="No im_class or __qualname__ support.")
requires_qualname = pytest.mark.skipif(sys.version_info < (3, 3), reason="Use requires __qualname__ support.")


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
	class Nested(object):
		pass
	
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
	def test__resolve__of_a_module_level_class_method(self):
		assert resolve(Example.classmethod) == 'test.test_util:Example.classmethod'
		assert resolve(Example().classmethod) == 'test.test_util:Example.classmethod'
	
	@requires_qualname
	def test__resolve__of_a_module_level_static_method(self):
		assert resolve(Example.staticmethod) == 'test.test_util:Example.staticmethod'
		assert resolve(Example().staticmethod) == 'test.test_util:Example.staticmethod'
	
	@requires_qualname
	def test__resolve__of_a_nested_class(self):
		assert resolve(self.Nested) == 'test.test_util:TestResolver.Nested'
	
	@requires_qualname
	def test__resolve__of_a_closure(self):
		def closure():
			pass
		
		assert resolve(closure) == 'test.test_util:TestResolver.test__resolve__of_a_closure.<locals>.closure'


def object_fails(obj):
	try:
		assert resolve(obj)
	except TypeError:
		pass
	else:
		assert False, "Failed to raise TypeError."

def test_acceptable_failure_scenarios():
	def closure():
		pass
	
	def Closure(object):
		pass
	
	if not bool(os.environ.get('CANARY', False)):
		yield object_fails, Example.instance
		yield object_fails, Example.classmethod
	
	if sys.version_info >= (3, 3):
		yield object_fails, Example.staticmethod
	
	else:
		yield object_fails, TestResolver.Nested
		yield object_fails, closure
		yield object_fails, Closure
		yield object_fails, Example.Pandora
		
		1/0
		assert not resolve(Example.Pandora)
