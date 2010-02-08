#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
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

import gobject
import inspect
import functools

from umit.pm.core.logger import log
from umit.pm.core.atoms import Singleton

class Service(gobject.GObject):
    __gtype_name__ = "Service"
    __gsignals__ = {
        'vfunc-registered' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                              (gobject.TYPE_STRING, )),
        'vfunc-deregistered' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                              (gobject.TYPE_STRING, )),
        'func-registered' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                             (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)),
        'func-deregistered' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                               (gobject.TYPE_STRING, )),
        'func-binded' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                         (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)),
        'func-unbinded' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                           (gobject.TYPE_STRING, )),
    }

    def __init__(self, svcid):
        self.id = svcid
        self.funcs = {}
        gobject.GObject.__init__(self)

    def register_vfunction(self, funcname):
        "Register a virtual function"
        if not funcname in self.funcs:
            self.funcs[funcname] = None
            self.emit('vfunc-registered', funcname)

            log.info('%s vfunction registered for %s' % (funcname, self.id))

    def register_function(self, funcname, cb):
        if not funcname in self.funcs or not self.funcs[funcname]:
            self.funcs[funcname] = cb
            self.emit('func-registered', funcname, cb)

            log.info('%s function registered for %s' % (funcname, self.id))
        else:
            raise ValueError("Function `%s' already registered" % funcname)

    def bind_function(self, funcname, func):
        if funcname in self.funcs and self.funcs[funcname] is None:
            self.funcs[funcname] = func
            self.emit('func-binded', funcname, func)
            log.info("Function %s binded as %s" % (func, funcname))
        else:
            raise ValueError("Service doesn't provide `%s' method" % \
                             funcname)

    def unbind_function(self, funcname):
        if funcname in self.funcs:
            self.funcs[funcname] = None
            self.emit('func-unbinded', funcname)
        else:
            raise ValueError("Service doesn't export `%s' method" % \
                             funcname)

    def get_function(self, funcname):
        return self.funcs[funcname]

    def call(self, funcname, *args, **kwargs):
        return self.funcs[funcname](*args, **kwargs)

class ServiceBus(Singleton, gobject.GObject):
    __gtype_name__ = "ServiceBus"
    __gsignals__ = {
        'registered' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                        (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT, )),
        'deregistered' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                          (gobject.TYPE_STRING, )),
    }

    def __init__(self):
        self.__svc = {}
        gobject.GObject.__init__(self)

    def get_service(self, svcid):
        return self.__svc.get(svcid, None)

    def deregister_service(self, svcid):
        if not svcid in self.__svc:
            raise KeyError("Service `%s' not registered" % svcid)

        del self.__svc[svcid]

        self.emit('deregistered', svcid)

    def register_service(self, svcid, obj):
        if svcid in self.__svc:
            raise ValueError("Service `%s' alredy registered" % svcid)

        self.__svc[svcid] = obj
        self.emit('registered', svcid, obj)

    # Utilities functions
    def get_function(self, svcid, funcname):
        return self.__svc[svcid].get_function(funcname)

    def call(self, svcid, funcname, *args, **kwargs):
        return self.__svc[svcid].call(funcname, *args, **kwargs)

# Decorators start here.

def register_interface(svcid):
    # Should be nice to have type checking or something li
    def export_imethods(svc):
        svc_inst = Service(svcid)
        ServiceBus().register_service(svcid, svc_inst)

        log.info("Registering new service INTERFACE `%s'" % svcid)

        for _, meth in inspect.getmembers(svc, inspect.ismethod):
            meth_name = meth.__name__

            if meth_name[0] == '_':
                continue

            svc_inst.register_vfunction(meth_name)
            log.info("Service has `%s' VFUNC" % meth_name)

        return svc
    return export_imethods

def export_methods(self, *args, **kwargs):
    cls = self.__class__
    cls.__init__ = cls.__original_init__

    svcid, implementor = cls.__svc_id__
    cls.__init__(self, *args, **kwargs)

    delattr(cls, '__svc_id__')
    delattr(cls, '__original_init__')

    if not implementor:
        log.info("Registering new service %s" % svcid)

        svc_inst = Service(svcid)
        ServiceBus().register_service(svcid, svc_inst)
    else:
        svc_inst = ServiceBus().get_service(svcid)

    if not svc_inst:
        return

    for _, meth in inspect.getmembers(self, inspect.ismethod):
        meth_name = meth.__name__

        if meth_name.startswith('__impl_'):
            if implementor:
                svc_inst.bind_function(meth_name[7:], meth)
            else:
                svc_inst.register_function(meth_name[7:], meth)

        elif not implementor and meth_name.startswith('__intf_'):
            svc_inst.register_vfunction(meth_name[7:])

def provides(svcid):
    def wrap(cls):
        cls.__original_init__ = cls.__init__
        cls.__init__ = export_methods

        setattr(cls, '__svc_id__', (svcid, False))
        return cls

    return wrap

def implements(svcid):
    def wrap(cls):
        cls.__original_init__ = cls.__init__
        cls.__init__ = export_methods

        setattr(cls, '__svc_id__', (svcid, True))
        return cls

    return wrap

class unbind_function(object):
    def __init__(self, svcid, funcname):
        self.svcid = svcid
        self.funcname = funcname

    def __call__(self, f):
        @functools.wraps(f)
        def wrap(*args, **kwargs):
            f(*args, **kwargs)

            svc_inst = ServiceBus().get_service(self.svcid)

            if svc_inst:
                if isinstance(self.funcname, (list, tuple)):
                    for func in self.funcname:
                        svc_inst.unbind_function(func)
                else:
                    svc_inst.unbind_function(self.funcname)

        return wrap

# Initialize services from here

def services_boot():
    @register_interface('pm.hostlist')
    class SvcHostList(object):
        """
        This service is used to share a list of hosts
        """
        def populate(self, interface): pass
        def info(self, intf, ip, mac): pass

        def get(self): pass
        def get_target(self, l2_addr=None, l3_addr=None, hostname=None, \
                       netmask=None): pass
