# encoding: utf-8

import os
import math
import pytest

from itertools import chain
from textwrap import TextWrapper

from marrow.cache.util import *


canaried = pytest.mark.skipif(bool(os.environ.get('CANARY', False)), reason="No im_class or __qualname__ support.")


class TestResolveStdlib(object):
	def test_basic(self):
		assert resolve(chain) == 'itertools:chain'
	
	def test_class(self):
		assert resolve(TextWrapper) == 'textwrap:TextWrapper'
	
	@canaried
	def test_method(self):
		assert resolve(TextWrapper.fill) == 'textwrap:TextWrapper.fill'


class TestResolveMarrowTask(object):
	def test_class(self):
		from marrow.cache import Cache
		assert resolve(Cache) == 'marrow.cache.model:Cache'
		assert resolve(Cache()) == 'marrow.cache.model:Cache'
	
	@canaried
	def test_method(self):
		from marrow.cache import Cache
		assert resolve(Cache().__repr__) == 'marrow.cache.model:Cache.__repr__'
		assert resolve(Cache.__repr__) == 'marrow.cache.model:Cache.__repr__'
	
	@canaried
	def test_class_method(self):
		from marrow.cache.model import CacheKey
		assert resolve(CacheKey.new) == 'marrow.cache.model:CacheKey.new'
