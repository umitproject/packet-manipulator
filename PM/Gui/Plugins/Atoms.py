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

"""
Contains atoms class used in various part of program
"""

class StringFile(str):
    """
    Dummy class to avoid reimplementing of GNUTranslations
    for file within a zip archive
    """

    def read(self):
        return self

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

class DepDict(dict):
    """
    Dummy class to have default list based dict
    
    >>> w = DepDict()
    >>> w["miao"]
    []
    >>> w["miao"] = 1
    >>> w["miao"]
    [1]
    >>> w["miao"] = 1
    >>> w["miao"]
    [1, 1]
    >>> w
    {'miao': [1, 1]}
    """

    def __getitem__(self, i):
        if i not in self:
            return []
        else:
            return super(DepDict, self).__getitem__(i)
    def __setitem__(self, i, x):
        if i not in self:
            super(DepDict, self).__setitem__(i, [])
        self[i].append(x)

class OperatorException(Exception):
    "A simple Exception class to track exception in Operator"
    pass

class Operator(object):
    """
    An operator class to compare Version objects


    >>> o = Operator(">")
    >>> o(Version("2"), Version("3"))
    False
    >>> o = Operator("<")
    >>> o(Version("2"), Version("3"))
    True
    >>> Operator("PWNED!")
    Traceback (most recent call last):
    OperatorException: Not valid operator
    >>> o(Version("2"), None)
    Traceback (most recent call last):
    VersionException: Must be a Version object
    """

    def __init__(self, op_str):
        self.op = None

        if op_str == "=":
            self.op = Version.__eq__
        elif op_str == ">":
            self.op = Version.__gt__
        elif op_str == "<":
            self.op = Version.__lt__
        elif op_str == "<=":
            self.op = Version.__le__
        elif op_str == ">=":
            self.op = Version.__ge__
        elif op_str == "!":
            self.op = Version.__ne__

        if not self.op and op_str != ".":
            raise OperatorException("Not valid operator")

        self.op_str = op_str

    def __call__(self, ver1, ver2):
        if self.op:
            return self.op(ver1, ver2)
        else:
            return None

    def __repr__(self):
        return "'%s'" % self.op_str

    def __eq__(self, other):
        return self.op_str == other.op_str
    def __ne__(self, other):
        return self.op_str != other.op_str

class VersionException(Exception):
    "A simple Exception class to track exception in Version"
    pass

class Version(object):
    """
    A class to manage package version

    >>> Version("2.0.0")
    2.0.0
    >>> Version("2") < Version("3")
    True
    >>> Version("2")
    2.0.0
    >>> Version("")
    (n/a)
    >>> Version("aaaaaaa")
    (n/a)
    >>> Version("-1.-1.-22")
    (n/a)
    >>> Version.__cmp__(Version("1.0.0"), 1)
    Traceback (most recent call last):
    VersionException: Must be a Version object
    """

    def __init__(self, ver_str):
        self.main = -1
        self.second = -1
        self.revision = -1

        try:
            t = ver_str.split(".", 2)

            self.main = int(t[0])
            self.second = int(t[1])
            self.revision = int(t[2])

            if self.main < 0 or self.second < 0 or self.revision < 0:
                self.main = -1
                self.second = -1
                self.revision = -1

        except:
            if self.main >= 0:
                if self.second < 0:
                    self.second = 0
                if self.revision < 0:
                    self.revision = 0

    def __repr__(self):
        if self.main < 0 and self.second < 0 and self.revision < 0:
            return "(n/a)"
        return "%d.%d.%d" % (self.main, self.second, self.revision)

    def __cmp__(self, other):
        if not isinstance(other, Version):
            raise VersionException("Must be a Version object")

        if self.main == other.main:
            if self.second == other.second:
                if self.revision == other.revision:
                    return 0
                else:
                    return int.__cmp__(self.revision, other.revision)
            else:
                return int.__cmp__(self.second, other.second)
        else:
            return int.__cmp__(self.main, other.main)

    def __lt__(self, other):
        return self.__cmp__(other) < 0
    def __le__(self, other):
        return self.__cmp__(other) <= 0
    def __eq__(self, other):
        return self.__cmp__(other) == 0
    def __ne__(self, other):
        return self.__cmp__(other) != 0
    def __gt__(self, other):
        return self.__cmp__(other) > 0
    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def empty(self):
        "Check if is empty"
        return self.main < 0 and self.second < 0 and self.revision < 0

    @staticmethod
    def stringify_version(name, operator, version):
        """
        @return a reasonable string representing the version.

        >>> Version.stringify_version("miao", Operator("."), Version(""))
        'miao-*'
        >>> Version.stringify_version("miao", Operator("."), Version("2.0.0"))
        'miao-*'
        >>> Version.stringify_version("miao", Operator("!"), Version("2.0.0"))
        '!miao-2.0.0'
        """

        if operator.op_str == '.' or version.empty():
            # we could skip the operator and version
            return "%s-*" % name
        else:
            return "%s%s-%s" % (str(operator).replace("'", ""), name, version)

    @staticmethod
    def extract_version(pkg_str):
        """
        @return a tuple (pkg_name, pkg_operator, pkg_version)

        >>> Version.extract_version("dummy-2.0")
        ('dummy', '=', 2.0.0)
        >>> isinstance(_[1], Operator), isinstance(_[2], Version)
        (True, True)
        >>> Version.extract_version("=dummy-2.0")
        ('dummy', '=', 2.0.0)
        >>> Version.extract_version("=-2.0.0")
        Traceback (most recent call last):
        VersionException: Malformed pkg_str
        >>> Version.extract_version("dummy<3")
        Traceback (most recent call last):
        VersionException: Malformed pkg_str
        >>> Version.extract_version("dummy3")
        ('dummy3', '.', (n/a))
        >>> Version.extract_version("<dummy-3")
        ('dummy', '<', 3.0.0)
        >>> Version.extract_version(">=dummy-2.0")
        ('dummy', '>=', 2.0.0)
        """


        # BNF: [op] <name> [version]
        # [op] is >= or > or = or <= or < or !
        # [version] is like 2.0.0

        # '=' segue '<' o '>'

        ops = (
            '>=',
            '<=',
            '=',
            '>',
            '<',
            '!'
        )

        name = ""
        version = Version("")
        operator = Operator("=")

        try:
            for op in ops:
                if op == pkg_str[0:len(op)]:
                    operator = Operator(op)
                    pkg_str = pkg_str[len(op):]

                    break
        except:
            pass

        try:
            t = pkg_str.split("-", 1)

            name = t[0]
            version = Version(t[1])
        except:
            pass

        if not name or not name.isalnum():
            raise VersionException("Malformed pkg_str")
        elif version == Version(""):
            return (name, Operator("."), version)
        else:
            return (name, operator, version)

# Not used
class Operators:
    EQ = Operator('=')
    NE = Operator('!')
    GT = Operator('>')
    GE = Operator('>=')
    LT = Operator('<')
    LE = Operator('<=')
    PS = Operator('.')

if __name__ == "__main__":
    Version.extract_version(">=dummy-2.0")
    import doctest
    doctest.testmod()
