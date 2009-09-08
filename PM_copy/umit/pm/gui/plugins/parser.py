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

import re

from xml.dom.minidom import parse, parseString, getDOMImplementation
from umit.pm.core.logger import log

class Variable(object):
    """
    A simple base class to create Variable that
    are stored in xml file
    """
    
    def __init__(self, value, \
                 name=None, def_value=None, desc=None, \
                 attrs=(), parent=None):
        """
        Create a variable

        @param value the value for variable
        @param name the name for variable (optional if are in list)
        @param def_val the default value for variable (optional if is user conf)
        @param desc the description of value (optional if in user conf)
        @param attrs a list of attributes
        @param sectiondict the section dict
        """
        self._value = self.__class__.convert(value)
        self._name = name
        self._def_val = self.__class__.convert(def_value)
        self._desc = desc
        self._parent = parent

        # Compatibility for child objects
        self.add_attribute(attrs, 'id', Integer, '_id')

        self.set_attributes(attrs)
        self.check_validity()

        if not Variable.setted(self._value):
            raise Exception("Value not setted")
        
        if not isinstance(self._value, self.__class__.element_type):
            raise Exception("Unable to set a valid type")
        
        log.debug(">>> Variable named '%s' allocate with value '%s'" % (self._name, self._value))

    @staticmethod
    def setted(value):
        "Just convenient method to check a value"
        return value is not None

    @staticmethod
    def convert(value, exc_on_error=False):
        """
        @param value the str value to be converted
        @param exc_on_error if an Exception should be raised on error
        """

        if isinstance(value, basestring):
            return value

        if exc_on_error:
            raise Exception("Cannot convert %s" % value)
        else:
            return None
    
    @staticmethod
    def revert(value, exc_on_error=False):
        """
        @param value a type that should be converted to str
        @param exc_on_error if an Exception should be raised on error
        """
        return str(value)

    def add_attribute(self, attrs, name, typ, varname):
        """
        Set the variable named varname in self

        @param attrs the attributes dict
        @param name the name of variable to be getted from dict
        @param type the variable object to be used for converting
        @param varname the variable name to be setted in self

        @return True if the var was setted and it's not None or
                False in case of not-setted variable
        """

        # Set to None for default
        setattr(self, varname, None)

        try:
            setattr(self, varname, typ.convert(attrs[name].nodeValue))
        except Exception:
            pass

        if getattr(self, varname) is not None:
            return True

        return False

    def set_attributes(self, attrs):
        """
        Ovverride this and call add_attribute
        """
        pass

    def check_validity(self):
        """
        Check the value validity and if fail set value to defaul
        """
        if not Variable.setted(self._value):
            log.debug("check_validity(): value is not setted. Falling back to default value")
            self._value = self._def_val
        elif not isinstance(self._value, self.__class__.element_type):
            log.debug("check_validity(): value is not of the type. Fallink back to default value")
            self._value = self._def_val
        elif not self.validate():
            log.debug("check_validity(): value is not valid for validate(). Fallink back to default value")
            self._value = self._def_val
        else:
            log.debug("check_validity(): value is OK")

        log.debug("check_validity(): Ends out value is '%s'" % self._value)

    def validate(self):
        """
        Validate the value or other fields for Variable
        
        @return True if value is ok or False
        """
        return True

    def __repr__(self):
        return "%s -> %s" % (self._name, self._value)

    def get_id(self):
        if not isinstance(self._id, int) and isinstance(self._parent, List):
            try:
                self._id = self._parent.list.index(self)
            except:
                pass

        return self._id

    def set_id(self, val):
        if isinstance(val, int) and isinstance(self._parent, List):
            self._id = val
            self._parent.update(self)

    def get_name(self):
        return self._name
    def set_name(self, val):
        if isinstance(val, basestring) and isinstance(self._parent, dict):
            self._parent.pop(self._name)
            self._name = val
            self._parent[self._name] = self

    def get_value(self):
        return self._value
    def set_value(self, val):
        if isinstance(val, self.__class__.element_type):
            self._value = val

    def get_desc(self):
        return self._desc
    def set_desc(self, val):
        if isinstance(val, basestring):
            self._desc = val

    # Common properties
    id = property(get_id, set_id)
    name = property(get_name, set_name)
    value = property(get_value, set_value)
    description = property(get_desc, set_desc)

class String(Variable):
    __var_names__ = ('string', 'str', 's')

    __attribs__ = ('max', 'min', 'pattern')
    __tattribs__ = (int, int, str)

    element_type = basestring

    def set_attributes(self, attribs):
        self._pattern_re = None
        self.add_attribute(attribs, 'min', Integer, '_min')
        self.add_attribute(attribs, 'max', Integer, '_max')

        # Compile pattern if it's setted
        if self.add_attribute(attribs, 'pattern', String, '_pattern'):
            try:
                self._pattern_re = re.compile(self._pattern)
            except Exception:
                pass

    def validate(self):
        if Variable.setted(self._min) and len(self._value) < self._min:
            return False
        if Variable.setted(self._max) and len(self._value) > self._max:
            return False
        if Variable.setted(self._pattern_re) and \
           not self._pattern_re.match(self._value):
            return False

        return True

    def get_min(self):
        return self._min
    def set_min(self, val):
        if isinstance(val, int):
            self._min = val
            self.check_validity()

    def get_max(self):
        return self._max
    def set_max(self, val):
        if isinstance(val, int):
            self._max = val
            self.check_validity()

    min = property(get_min, set_min)
    max = property(get_max, set_max)

    def get_pattern(self):
        return self._pattern
    def set_pattern(self, val):
        if isinstance(val, basestring):
            try:
                r = re.compile(val)
                self._pattern = val
                self._pattern_re = r
            except Exception:
                pass
            self.check_validity()

    pattern = property(get_pattern, set_pattern)

class Integer(Variable):
    __var_names__ = ('integer', 'int', 'i')

    __attribs__ = ('max', 'min')
    __tattribs__ = (int, int)

    element_type = int

    @staticmethod
    def convert(value, exc_on_error=False):
        if isinstance(value, basestring):
            try:
                return int(value)
            except Exception:
                pass

        if exc_on_error:
            return Exception("Cannot convert %s to float" % value)
        else:
            return None

    def set_attributes(self, attribs):
        self.add_attribute(attribs, 'min', Integer, '_min')
        self.add_attribute(attribs, 'max', Integer, '_max')

    def validate(self):
        if Variable.setted(self._min) and self._value < self._min:
            return False
        if Variable.setted(self._max) and self._value > self._max:
            return False

        return True

    def get_min(self):
        return self._min
    def set_min(self, val):
        if isinstance(val, self.__class__.element_type):
            self._min = val
            self.check_validity()

    def get_max(self):
        return self._max
    def set_max(self, val):
        if isinstance(val, self.__class__.element_type):
            self._max = val
            self.check_validity()

    min = property(get_min, set_min)
    max = property(get_max, set_max)

class Float(Integer):
    __var_names__ = ('float', 'flt', 'f')

    __attribs__ = ('min', 'max')
    __tattribs__ = (float, float)

    element_type = float

    @staticmethod
    def convert(value, exc_on_error=False):
        if isinstance(value, basestring):
            try:
                return float(value)
            except Exception:
                pass

        if exc_on_error:
            return Exception("Cannot convert %s to float" % value)
        else:
            return None

    def set_attributes(self, attribs):
        self.add_attribute(attribs, 'min', Float, '_min')
        self.add_attribute(attribs, 'max', Float, '_max')

class Boolean(Variable):
    __var_names__ = ('boolean', 'bool', 'b')
    
    __attribs__ = ()
    __tattribs__ = ()

    element_type = bool

    @staticmethod
    def convert(value, exc_on_error=False):
        if isinstance(value, basestring):
            if value == '1' or value.upper() == 'TRUE':
                return True
            if value == '0' or value.upper() == 'FALSE':
                return False

        if exc_on_error:
            return Exception("Cannot convert %s to bool" % value)
        else:
            return None

    @staticmethod
    def revert(value, exc_on_error=False):
        return (value) and ('true') or ('false')

class List(Variable):
    "max/min/pattern/maxe/mine -> id"
    __var_names__ = ('list', 'lst', 'l')

    __attribs__ = ('min', 'max', 'minelements', 'maxelements', 'pattern')
    __tattribs__ = (int, int, int, int, str)

    element_type = list

    def __init__(self, value, \
                 name=None, def_value=None, desc=None, \
                 attrs=(), childs=(), dict=None):
        try:
            Variable.__init__(self, value, name, def_value, desc, attrs, dict)
        except Exception, err:
            pass

        for child in childs:
            try:
                obj = Parser.create_var(child, self)

                if not Variable.setted(self._type):
                    self._type = type(obj)

                if not isinstance(obj, self._type):
                    continue

                if Variable.setted(obj.id):
                    self._list.insert(obj.id, obj)
                else:
                    self._list.append(obj)

            except Exception, err:
                continue

        self.check_validity()

    def set_attributes(self, attribs):
        self._list = []
        self._pattern_re = None

        self.add_attribute(attribs, 'min', Integer, '_min')
        self.add_attribute(attribs, 'max', Integer, '_max')
        self.add_attribute(attribs, 'min-elements', Integer, '_lmin')
        self.add_attribute(attribs, 'max-elements', Integer, '_lmax')

        if self.add_attribute(attribs, 'pattern', String, '_pattern'):
            try:
                self._pattern_re = re.compile(self._pattern)
            except Exception:
                pass

        # We must get the type attribute
        try:
            self._type = Parser.get_type(attribs['type'].nodeValue)
        except Exception:
            self._type = None

    def check_validity(self):
        # Becouse value cannot be setted in list object
        # this is only an empty function that call validate
        if self._list and not self.validate():
            self._list.clear()

    def validate(self):
        ret = []

        for elem in self._list:
            if Variable.setted(self._max) and len(elem.value) > self._max:
                continue
            if Variable.setted(self._min) and len(elem.value) < self._min:
                continue
            if self._type == String and \
               Variable.setted(self._pattern_re) and self._pattern and \
               not self._pattern_re.match(elem.value):
                continue
            ret.append(elem)

        self._list = ret

        if Variable.setted(self._lmax) and len(self._list) > self._lmax:
            return False
        if Variable.setted(self._lmin) and len(self._list) < self._lmin:
            return False

        return True
    
    def update(self, obj):
        self._list.remove(obj)
        self._list.insert(obj.id, obj)

    def __repr__(self):
        return "%s -> %s" % (self._name, self._list)

    def __getitem__(self, idx):
        return self._list[idx]

    list = property(lambda x: x._list)

    # Attributes

    def get_min(self):
        return self._min
    def set_min(self, val):
        if isinstance(val, int):
            self._min = val
            self.check_validity()

    def get_max(self):
        return self._max
    def set_max(self, val):
        if isinstance(val, int):
            self._max = val
            self.check_validity()

    min = property(get_min, set_min)
    max = property(get_max, set_max)

    def get_lmin(self):
        return self._lmin
    def set_lmin(self, val):
        if isinstance(val, int):
            self._lmin = val
            self.check_validity()

    def get_lmax(self):
        return self._lmax
    def set_lmax(self, val):
        if isinstance(val, int):
            self._lmax = val
            self.check_validity()

    minelements = property(get_lmin, set_lmin)
    maxelements = property(get_lmax, set_lmax)

    def get_pattern(self):
        return self._pattern
    def set_pattern(self, val):
        if isinstance(val, basestring):
            try:
                r = re.compile(val)
                self._pattern = val
                self._pattern_re = r
            except Exception:
                pass
            self.check_validity()

    pattern = property(get_pattern, set_pattern)

class Parser(object):
    TYPES = (
        String,
        Integer,
        Float,
        Boolean,
        List
    )

    TRANSLATOR = {
        str : String,
        int : Integer,
        float : Float,
        bool : Boolean,
        list : List
    }

    def __getitem__(self, x):
        return self.sections[x]

    def __init__(self):
        self.sections = {}
    def save_to_file(self, fname):
        doc = self.create_doc()
        
        f = open(fname, "w")
        f.write(doc.toprettyxml('  '))
        f.close()

    def create_doc(self):
        doc = getDOMImplementation().createDocument(None, "preferences", None)

        keys = self.sections.keys()
        keys.sort()

        for sname in keys:
            section = self.sections[sname]

            sec_element = doc.createElement('section')
            sec_element.setAttribute('name', sname)
            doc.documentElement.appendChild(sec_element)

            self.dump_section(doc, sec_element, section)

        return doc

    def dump_section(self, doc, element, section):
        keys = section.keys()
        keys.sort()

        for vname in keys:
            var = section[vname]

            child = doc.createElement(var.__var_names__[-1])

            for attr in ('name', 'value', 'default', 'description') + \
                         var.__attribs__:
                attr_val = getattr(var, attr, None)

                if attr_val is not None:
                    if not isinstance(attr_val, basestring):
                        attr_val = Parser.TRANSLATOR[type(attr_val)].revert(attr_val)
                    child.setAttribute(attr, attr_val)

            element.appendChild(child)

    def parse_string(self, txt):
        self.parse_doc(parseString(txt))
    def parse_file(self, path):
        self.parse_doc(parse(path))
    def parse_doc(self, doc):
        if not doc.documentElement.tagName == "preferences":
            return 

        for node in doc.documentElement.childNodes:
            if node.nodeName == "section":
                self.parse_section(node)
    def parse_section(self, node):
        if not node or \
           not node.attributes.has_key('name') or \
           not node.attributes['name'].nodeValue:
            return

        section_name = node.attributes['name'].nodeValue

        if not section_name in self.sections:
            self.sections[section_name] = {}

        section_dict = self.sections[section_name]

        for n in node.childNodes:
            try:
                obj = self.create_var(n, section_dict)
                section_dict[obj.name] = obj
            except Exception, err:
                continue

    @staticmethod
    def create_var(node, sdict):
        name = node.nodeName
        type = Parser.get_type(name)

        if not type:
            raise Exception("Not a valid type")

        # We need to get various fields

        name  = Parser.get_attribute(node, 'name')
        val   = Parser.get_attribute(node, 'value')
        deflt = Parser.get_attribute(node, 'default')
        descr = Parser.get_attribute(node, 'description')

        # We are atomic variable so we *MUST* have setted
        # at least a name and a value/default value
        if isinstance(sdict, dict):
            if not Variable.setted(name):
                raise Exception("No name setted for atomic variable")

            if type == List:
                return type( \
                    None, name, None, descr, \
                    node.attributes, node.childNodes, sdict \
                )

        # For child variables only a value/default value
        conv = type.convert

        if not Variable.setted(conv(val)) and not Variable.setted(conv(deflt)):
            raise Exception("No value/default setted for atomic variable")

        return type(val, name, deflt, descr, node.attributes, parent=sdict)

    @staticmethod
    def get_attribute(node, value):
        try:
            return node.attributes[value].nodeValue
        except Exception:
            return None

    @staticmethod
    def get_type(name):
        for type in Parser.TYPES:
            if name in type.__var_names__:
                return type
        return None

if __name__ == "__main__":
    p = Parser()
    p.parse_file("test.xml")
    o = p["General"]["bool1"]
    p["General"]["bool1"].name = "booooool"
    print p["General"]["booooool"]
    print p["General"]["booooool"] is o

    print p["General"]["default-list"]
    p["General"]["default-list"][2].id = 0
    print p["General"]["default-list"]

    print p["General"]["default-list"][1].id
