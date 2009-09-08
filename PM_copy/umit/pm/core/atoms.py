#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009 Adriano Monteiro Marques
#
# Author: Francesco Piccinno <stack.box@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

"""
This module contains class that could be useful in various parts of the
program
"""

import sys
import copy
import Queue
import threading

import StringIO
import traceback

from HTMLParser import HTMLParser

from umit.pm.core.logger import log

try:
    from collections import defaultdict
except ImportError:
    class defaultdict(dict):
        def __init__(self, default_factory=None, *a, **kw):
            if (default_factory is not None and
                not hasattr(default_factory, '__call__')):
                raise TypeError('first argument must be callable')
            dict.__init__(self, *a, **kw)
            self.default_factory = default_factory
        def __getitem__(self, key):
            if key in self:
                return dict.__getitem__(self, key)
            else:
                return self.__missing__(key)
        def __missing__(self, key):
            if self.default_factory is None:
                raise KeyError(key)
            self[key] = value = self.default_factory()
            return value
        def __reduce__(self):
            if self.default_factory is None:
                args = tuple()
            else:
                args = self.default_factory,
            return type(self), args, None, None, self.iteritems()
        def copy(self):
            return self.__copy__()
        def __copy__(self):
            return type(self)(self.default_factory, self)
        def __deepcopy__(self, memo):
            import copy
            return type(self)(self.default_factory,
                              copy.deepcopy(self.items()))
        def __repr__(self):
            return 'defaultdict(%s, %s)' % (self.default_factory,
                                            dict.__repr__(self))

# Ordered dict python implementation

class odict(dict):

    def __init__(self, d={}):
        self._keys = d.keys()
        dict.__init__(self, d)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._keys.remove(key)

    def __setitem__(self, key, item):
        dict.__setitem__(self, key, item)
        # a peculiar sharp edge from copy.deepcopy
        # we'll have our set item called without __init__
        if not hasattr(self, '_keys'):
            self._keys = [key,]
        if key not in self._keys:
            self._keys.append(key)

    def clear(self):
        dict.clear(self)
        self._keys = []

    def items(self):
        items = []
        for i in self._keys:
            items.append(i, self[i])
        return items

    def keys(self):
        return self._keys

    def popitem(self):
        if len(self._keys) == 0:
            raise KeyError('dictionary is empty')
        else:
            key = self._keys[-1]
            val = self[key]
            del self[key]
            return key, val

    def setdefault(self, key, failobj = None):
        dict.setdefault(self, key, failobj)
        if key not in self._keys:
            self._keys.append(key)

    def update(self, d):
        for key in d.keys():
            if not self.has_key(key):
                self._keys.append(key)
        dict.update(self, d)

    def values(self):
        v = []
        for i in self._keys:
            v.append(self[i])
        return v

    def move(self, key, index):

        """ Move the specified to key to *before* the specified index. """

        try:
            cur = self._keys.index(key)
        except ValueError:
            raise KeyError(key)
        self._keys.insert(index, key)
        # this may have shifted the position of cur, if it is after index
        if cur >= index: cur = cur + 1
        del self._keys[cur]

    def index(self, key):
        if not self.has_key(key):
            raise KeyError(key)
        return self._keys.index(key)

    def __iter__(self):
        for k in self._keys:
            yield k

# Simple decorator for compatibility with python 2.4 (with statement)
def with_decorator(func):
    def proxy(self, *args, **kwargs):
        self.lock.acquire()

        try:
            return func(self, *args, **kwargs)
        finally:
            self.lock.release()

    proxy.__name__ = func.__name__
    proxy.__dict__ = func.__dict__
    proxy.__doc__ = func.__doc__

    return proxy

def generate_traceback():
    fp = StringIO.StringIO()
    traceback.print_exc(file=fp)
    return fp.getvalue()

class Node(object):
    """
    A simple Node class to create Binary tree.
    To create a tree simply do tree = Node()
    """

    def __init__(self, data=None, children=[]):
        """
        Initialize a Node object
        @param data the data for the Node or None if you are constructing
               a Tree object
        @param children a list of Node objects
        """

        self.data = data
        self.root = None
        self.children = []

        for child in children:
            self.append_node(child)

    def append_node(self, node):
        """
        Append a child node
        @param node a Node object
        """

        assert (isinstance(node, Node))

        node.root = self
        self.children.append(node)

    def __iter__(self):
        if self.data:
            yield self

        for child in self.children:
            for c in child:
                yield c

    def __repr__(self):
        if self.root != None:
            return "%sChild -> %s (%d)" % ("  " * self.get_depth(), self.data,
                                           len(self.children))
        else:
            return "Tree %s" % object.__repr__(self)

    def get_depth(self):
        idx = 0
        root = self.root

        while root:
            root = root.root
            idx += 1

        return idx

    def __len__(self):
        tot = 0
        for node in self.children:
            tot += len(node)

        if self.data:
            tot += 1

        return tot

    def get_parent(self):
        return self.root

    def get_data(self):
        return self.data

    def get_children(self):
        for node in self.children:
            yield node

    def is_parent(self):
        return self.children != []

    def __getitem__(self, x):
        return self.children[x]

    def find(self, value):
        for i in self:
            if value == i.data:
                return i.get_path()

        return None

    def get_path(self):
        path = []

        find = self
        root = self.root

        while root:
            path.append(root.index(find))

            root = root.root
            find = find.root

        path.reverse()
        return tuple(path)

    def get_next_of(self, node):
        try:
            return self[self.index(node) + 1]
        except:
            return None

    def index(self, node):
        return self.children.index(node)

    def get_from_path(self, path):
        root = self

        for idx in path:
            root = root[idx]

        return root

    def sort(self):
        for node in self.children:
            node.sort()

        self.children.sort()

    def __cmp__(self, node):
        if not self:
            return 1
        if not node:
            return -1
        return cmp(self.data, node.data)

WorkerStop = object()

class ThreadPool(object):
    MIN_THREADS = 5
    MAX_THREADS = 20
    IS_DAEMON = True

    started = False
    joined = False
    workers = 0

    def __init__(self, minthreads=5, maxthreads=20):
        assert minthreads >= 0
        assert minthreads <= maxthreads

        self.queue = Queue.Queue(0)
        self.min = minthreads
        self.max = maxthreads

        self.waiters = []
        self.threads = []
        self.working = []

    def queue_work(self, callback, errback, func, *args, **kwargs):
        if self.joined:
            return

        obj = (callback, errback, func, args, kwargs)
        self.queue.put(obj)

        if self.started:
            self.resize()

    def start(self):
        self.joined = False
        self.started = True

        self.resize()

    def stop(self):
        self.joined = True
        threads = copy.copy(self.threads)

        while self.workers:
            self.queue.put(WorkerStop)
            self.workers -= 1

    def join_threads(self):
        # check out for exceptions on already joined
        # threads.

        threads = copy.copy(self.threads)

        for thread in threads:
            thread.join()

    def resize(self, minthreads=None, maxthreads=None):
        minthreads = max(minthreads, self.MIN_THREADS)
        maxthreads = max(minthreads, self.MAX_THREADS)

        assert minthreads >= 0
        assert minthreads <= maxthreads

        self.min = minthreads
        self.max = maxthreads

        if not self.started:
            return

        while self.workers > self.max:
            self.stop_worker()

        while self.workers < self.min:
            self.start_worker()

        self.start_needed_workers()

    def start_needed_workers(self):
        size = self.queue.qsize() + len(self.working)

        while self.workers < min(self.max, size):
            self.start_worker()

    def start_worker(self):
        self.workers += 1
        thread = threading.Thread(target=self._worker)
        thread.setDaemon(self.IS_DAEMON)

        self.threads.append(thread)
        thread.start()

    def stop_worker(self):
        self.queue.put(WorkerStop)
        self.workers -= 1

    def _worker(self):
        ct = threading.currentThread()
        obj = self.queue.get()

        while obj is not WorkerStop:
            self.working.append(ct)

            (callback, errback, func, args, kw) = obj

            try:
                try:
                    result = func(*args, **kw)
                except Exception, exc:
                    log.error("Handling exception %s Traceback:" % exc)
                    log.error(generate_traceback())

                    if errback is not None:
                        errback(sys.exc_info()[1])
                else:
                    if callback is not None:
                        callback(result)
            except Exception, err:
                log.critical("Thread exceptions ignored. Traceback:")
                log.critical(generate_traceback())

            self.working.remove(ct)

            self.waiters.append(ct)

            obj = self.queue.get()
            self.waiters.remove(ct)

        self.threads.remove(ct)

class Interruptable:
    """
    Interruptable interface
    """

    def start(self):
        raise Exception("Implement me")
    def terminate(self):
        raise Exception("Implement me")
    def isAlive(self):
        raise Exception("Implement me")

class Singleton(object):
    """
    A class for singleton pattern
    Support also gobject if Singleton base subclass if specified first
    """

    instances = {}
    def __new__(cls, *args, **kwargs):
        from gobject import GObject

        if Singleton.instances.get(cls) is None:
            cls.__original_init__ = cls.__init__
            if issubclass(cls, GObject):
                Singleton.instances[cls] = GObject.__new__(cls)
            else:
                Singleton.instances[cls] = object.__new__(cls, *args, **kwargs)
        elif cls.__init__ == cls.__original_init__:
            def nothing(*args, **kwargs):
                pass
            cls.__init__ = nothing
        return Singleton.instances[cls]

class HTMLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_stripped_data(self):
        return ''.join(self.fed)

def strip_tags(x):
    s = HTMLStripper()
    s.feed(x)
    return s.get_stripped_data()

__all__ = ['strip_tags', 'Singleton', 'Interruptable', 'ThreadPool', 'Node', \
           'generate_traceback', 'with_decorator', 'defaultdict', 'odict']
