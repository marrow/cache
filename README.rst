============
Marrow Cache
============

    © 2014-2015 Alice Bevan-McGregor and contributors.

..

    https://github.com/marrow/cache

..

    |latestversion| |downloads| |masterstatus| |mastercover| |masterrequires| |climate| |issuecount|

1. What is Marrow Cache?
========================

Marrow Cache is a light-weight transparent caching system for memoizing functions and MongoEngine Document model
methods.  It is fully tested and highly focused to this task.  Primary features include:

* "Memoize" the result of arbitrary function calls.

* Organize cached values into "prefixes".

* Intelligently cache the result of Document method calls, with the cached value bound to the primary key of the
  document; optionally also keying on other fields.

A TTL index in MongoDB will automatically cull expired values once a minute.  If overwhelmed, it won't be able to do
them all in one pass.  Incremental garbage collection is automatically accounted for by validating the expiry time
on any potential cache hit.  If invalid, the record will be explicitly deleted and a new one generated.

Be aware of MongoDB's `power of 2 sized allocations <http://docs.mongodb.org/manual/core/storage/#power-of-2-allocation>`_.


2. Installation
===============

Installing ``marrow.cache`` is easy, just execute the following in a terminal::

    pip install marrow.cache

**Note:** We *strongly* recommend always using a container, virtualization, or sandboxing environment of some kind when
developing using Python; installing things system-wide is yucky (for a variety of reasons) nine times out of ten.  We prefer light-weight `virtualenv <https://virtualenv.pypa.io/en/latest/virtualenv.html>`_, others prefer solutions as robust as `Vagrant <http://www.vagrantup.com>`_.

If you add ``marrow.cache`` to the ``install_requires`` argument of the call to ``setup()`` in your applicaiton's
``setup.py`` file, Marrow Cache will be automatically installed and made available when your own application or
library is installed.  We recommend using "less than" version numbers to ensure there are no unintentional
side-effects when updating.  Use ``marrow.cache<1.1`` to get all bugfixes for the current release, and
``marrow.cache<2.0`` to get bugfixes and feature updates while ensuring that large breaking changes are not installed.

**Remember to build the indexes.**  Executing ``Cache.ensure_indexes()`` in a shell after first deployment will do so.
If you forget and begin to cache data, refer to the `MongoEngine
documentation <http://docs.mongoengine.org/apireference.html#mongoengine.Document.ensure_index>`_ on building indexes
in the background.

2.1. Development Version
------------------------

    |developstatus| |developcover| |developrequires|

Development takes place on `GitHub <https://github.com/>`_ in the
`marrow.cache <https://github.com/marrow/cache/>`_ project.  Issue tracking, documentation, and downloads
are provided there.

Installing the current development version requires `Git <http://git-scm.com/>`_, a distributed source code management
system.  If you have Git you can run the following to download and *link* the development version into your Python
runtime::

    git clone https://github.com/marrow/cache.git
    (cd cache; python setup.py develop)

You can then upgrade to the latest version at any time::

    (cd cache; git pull; python setup.py develop)

If you would like to make changes and contribute them back to the project, fork the GitHub project, make your changes,
and submit a pull request.  This process is beyond the scope of this documentation; for more information see
`GitHub's documentation <http://help.github.com/>`_.


3. Functional Interface
=======================

Given you have a function that is expensive to execute you can use the Marrow Cache functional interface to
automatically preserve the result for more rapid recall on subsequent calls.

There are some important notes regarding behaviour:

* Arguments to the "generation" function are hashed after being passed through ``pprint``; collisions may occur.
  This can be alleviated by ensuring reasonable ``__repr__`` implementations or participation in the pretty-print
  protocol.

* The returned (and hence cached) values must be encodeable as a DynamicField, i.e. it must map to a BSON type.
  Some transformations may occur; subclasses of ``dict`` will return as an instance of the subclass on cache miss,
  only to be returned as an actual ``dict`` instance on cache hit.  See the examples for an approach that works
  around this.

The most basic approach is a function that takes arguments, does something to them, and returns a result::

    from marrow.cache import Cache
    
    @Cache.memoize(minutes=1)
    def multiply(x, y):
        return x * y

The ``memoize`` decorator takes the same named arguments as ``timedelta``, and defaults to a one week period.  The full
argument specification is as follows::

    Cache.memoize(
            prefix = None,  # defaults to callable's qualified name
            reference = None,  # ObjectId or saved Document instance, optional
            expires = datetime.utcnow,  # you can override the expiry time point of reference
            
            # timedelta values used against the expiry time during generation
            weeks = 0,  # actually defaults to 1, but not if anything else is defined
            days = 0,
            hours = 0,
            minutes = 0,
            seconds = 0,
            
            refresh = False  # automatically re-calculate and update the expiry time
        )

In our example, a call such as ``print(multiply(2, 4))`` will generate a MongoDB record like the following::

    {
        _id: {
                p: '__main__.multiply',
                r: None,
                hash: '... hash of arguments ...'
            },
        v: 8,
        e: now() + timedelta(minutes=1)
    }

If attempting to cache the result of an unreachable function (i.e. most closures) you must supply a prefix.

The original decorated function is available (to bypass caching) using the ``__func__`` attribute.

3.1. Cache Control
------------------

The decorated function is given an attribute that when dereferenced becomes a QuerySet mapping to the cached values
relevant to that callable.  It can be further queried, cleared, etc.


4. Object-Oriented Interface
============================

There is a second decorator that is method-aware.  It takes the same arguments as the ``memoize`` decorator, but only
as positional parameters.  It has a simple definition::

    Cache.method(*attributes, **kw)

Positional arguments may be strings referring to attributes pulled from the first argument passed to the callable.
Presumably this will be a ``self`` or ``cls`` refernece.  These may be nested using dot-notation, with attributes
tried first, then array dereferencing.  (Numerical values will be array dereferenced regardless.)

For example, to make the value cached automatically dependant on the ``x`` attribute of the instance::

    from marrow.schema import Container, Attribute
    
    class Multiply(Container):
        x = Attribute()
        
        @Cache.method('x', minutes=1)
        def do(self, y):
            return self.x * y

If the first argument (``self``, etc.) is a saved Document instance, ``pk`` will be automatically included in the
dependant attribute list.


5. Version History
==================

Version 1.0
-----------

* **Initial release.**  Extract from `Illico Hodes <http://www.illicohodes.com/>`_ RITA project.

Version 1.0.1
-------------

* **Timezone issue correction.**  Now correctly handles when timezone-awareness is enabled in MongoEngine/pymongo.

Version 1.0.2
-------------

* **Automatic prefix naming.** Automatic prefixes are now available on Python versions < 3.3.


6. License
==========

Marrow Cache has been released under the MIT Open Source license.

6.1. The MIT License
--------------------

Copyright © 2014-2015 Alice Bevan-McGregor and contributors.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the “Software”), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


.. |masterstatus| image:: http://img.shields.io/travis/marrow/cache/master.svg?style=flat
    :target: https://travis-ci.org/marrow/cache
    :alt: Release Build Status

.. |developstatus| image:: http://img.shields.io/travis/marrow/cache/develop.svg?style=flat
    :target: https://travis-ci.org/marrow/cache
    :alt: Development Build Status

.. |masterrequires| image:: https://requires.io/github/marrow/cache/requirements.svg?branch=master
    :target: https://requires.io/github/marrow/cache/requirements/?branch=master
    :alt: Package Requirements

.. |developrequires| image:: https://requires.io/github/marrow/cache/requirements.svg?branch=develop
    :target: https://requires.io/github/marrow/cache/requirements/?branch=develop
    :alt: Package Requirements

.. |latestversion| image:: http://img.shields.io/pypi/v/marrow.cache.svg?style=flat
    :target: https://pypi.python.org/pypi/cache
    :alt: Latest Version

.. |downloads| image:: http://img.shields.io/pypi/dw/marrow.cache.svg?style=flat
    :target: https://pypi.python.org/pypi/cache
    :alt: Downloads per Week

.. |mastercover| image:: http://img.shields.io/coveralls/marrow/cache/master.svg?style=flat
    :target: https://travis-ci.org/marrow/cache
    :alt: Release Test Coverage

.. |developcover| image:: http://img.shields.io/coveralls/marrow/cache/develop.svg?style=flat
    :target: https://travis-ci.org/marrow/cache
    :alt: Development Test Coverage

.. |issuecount| image:: http://img.shields.io/github/issues/marrow/cache.svg?style=flat
    :target: https://github.com/marrow/cache/issues
    :alt: Github Issues

.. |climate| image:: https://codeclimate.com/github/marrow/cache/badges/gpa.svg
    :target: https://codeclimate.com/github/marrow/cache
    :alt: Code Climate

.. |cake| image:: http://img.shields.io/badge/cake-lie-1b87fb.svg?style=flat
