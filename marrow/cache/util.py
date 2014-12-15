# encoding: utf-8

"""Convienent utilities."""

from __future__ import print_function

# ## Imports

from warnings import warn
from weakref import ref
from functools import wraps
from itertools import chain
from inspect import getmembers, getmodule, isclass, isfunction, ismethod
from collections import deque
from contextlib import contextmanager
from hashlib import sha256
from datetime import datetime, timedelta
from pprint import pformat
from marrow.package.canonical import name as resolve
from marrow.package.loader import traverse as fetch


# ## Weird Aliases

utcnow = datetime.utcnow


# ## Context Managers

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
