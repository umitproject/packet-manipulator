#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008 Adriano Monteiro Marques
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
