# encoding: utf-8

from marrow.cache.util import stack



def test_stack():
	class Example(object):
		pass
	
	assert not hasattr(Example, 'stack')
	
	with stack(Example, 'stack', 27):
		assert hasattr(Example, 'stack')
		assert list(Example.stack) == [27]
		
		with stack(Example, 'stack', 42):
			assert list(Example.stack) == [27, 42]
		
		assert list(Example.stack) == [27]
	
	assert not hasattr(Example, 'stack')
