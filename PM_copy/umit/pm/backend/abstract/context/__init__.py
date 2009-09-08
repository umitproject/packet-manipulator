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
In this module are defined:
    - register_static_context
    - register_timed_context
    - register_send_context
    - register_send_receive_context
    - register_sniff_context
    - register_sequence_context
    - register_audit_context

respectively to hook the contexts StaticContext, TimedContext,
SendContext, SendReceiveContext, SniffContext, SequenceContext and
AuditContext class creation.

It accepts as argument a BaseContext class objects defined in
Abstact/BaseContext and should return a new class object that
subclass this abstract class passed as argument to be valid.

So in your backend you should override this functions
if you want to customize the base context classes.

See also Scapy directory for reference.
"""

from umit.pm.core.logger import log

def register_static_context(context_class):
    "Override this to create your own StaticContext"

    log.debug("StaticContext not overloaded")
    return context_class

def register_timed_context(context_class):
    "Override this to create your own TimedContext"

    log.debug("TimedContext not overloaded")
    return context_class

def register_send_context(context_class):
    "Override this to create your own SendContext"

    log.debug("SendContext not overloaded")
    return context_class

def register_send_receive_context(context_class):
    "Override this to create your own SendReceiveContext"

    log.debug("SendReceiveContext not overloaded")
    return context_class

def register_sniff_context(context_class):
    "Override this to create your own SniffContext"

    log.debug("SniffContext not overloaded")
    return context_class

def register_sequence_context(context_class):
    "Override this to create your own SequenceContext"

    log.debug("SequenceContext not overloaded")
    return context_class

def register_audit_context(context_class):
    "Override this to create your own AuditContext"

    log.debug("AuditContext not overloaded")
    return context_class

from umit.pm.manager.preferencemanager import Prefs

if Prefs()['backend.system'].value.lower() == 'umpa':
    from umit.pm.backend.umpa.context import *
else:
    from umit.pm.backend.scapy.context import *
