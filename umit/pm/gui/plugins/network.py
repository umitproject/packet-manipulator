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
Module for network operations
"""

import urllib2
from threading import Thread

from umit.pm.core.i18n import _
from umit.pm.core.logger import log

#
# Simple decorators

def threaded(func):
    "Provides a thread decorator"
    def proxy(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.setDaemon(True)
        thread.start()
        return thread
    return proxy

def safecall(func):
    "Provides a safe decorator"
    def proxy(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception, err:
            log.error(_('>>> safecall(): Ignoring exception %s -> %s (%s, %s)')\
                      % (err, func, args, kwargs))
    return proxy

#
# Exceptions

class NetException(Exception):
    "Base class for other *NetException"
    pass

class ErrorNetException(NetException):
    "Raised when errors occured while downloading"
    def __init__(self, obj):
        NetException.__init__(self)

        self.args = obj.args

        # FIXME: check this
        if isinstance(obj, urllib2.HTTPError):
            self.reason = '%d %s' % (obj.code, obj.msg)
        else:
            try:
                self.reason = obj.reason
            except:
                self.reason = str(obj)

class StartNetException(NetException):
    "Raised when download is started"
    pass

class StopNetException(NetException):
    "Raised when download is completed"
    pass

#
# The engine for network operations

class Network(object):
    """
    A dummy class for asyncronous and threaded network operations
    """

    @staticmethod
    @threaded
    def get_url(url, cb, udata=None):
        """
        The callback should be of type

        callback(file, data, exception, userdata)

        file is a file-like object with two additional methods:
        - geturl() -- return the URL of the resource retrieved
        - info() -- return the meta-information of the page, as dictionary-like object

        exception is None if the operation has no error

        Remember that the callback is called within an external thread context

        @param url the url to get
        @param cb is the callback
        @param udata the additional data to pass to the callback
        """

        log.debug(_(">>> Calling get_url() for %s") % url)

        ufile = None

        @safecall
        def callback(file, data, exception, udata):
            cb(file, data, exception, udata)

        try:
            ufile = urllib2.urlopen(url)
            callback(ufile, None, StartNetException(), udata)

            for data in urllib2.urlopen(url):
                callback(ufile, data, None, udata)

            callback(ufile, None, StopNetException(), udata)

        except Exception, err:
            callback(ufile, None, ErrorNetException(err), udata)

        return

def test():
    "Stupid test function"

    def callback(ufile, data, exc, udata):
        if not exc:
            udata.append(data)
            len("".join(data))
            return

        if isinstance(exc, StartNetException):
            print "Getting file", ufile.geturl()
            return

        if isinstance(exc, StopNetException):
            print "Ok finished"
            print "Report hook called", len(udata), "times"
            print len("".join(udata)), "bytes"
            import md5
            m = md5.new()
            m.update("".join(udata))
            print "MD5", m.hexdigest()

            return

        if isinstance(exc, ErrorNetException):
            print "!!!", exc

    data = list()
    Network.get_url( \
            "http://localhost/~stack/plugins/systeminfo/SystemInfo.ump", \
            callback, data)

if __name__ == "__main__":
    test()
