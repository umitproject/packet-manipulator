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
import gtk
import pango

import base64
import string

try:
    from hashlib import md5
    from hashlib import sha1
    from hashlib import sha256

    SHA256_ENABLED = True

except ImportError:
    from md5 import md5
    from sha import sha as sha1

    SHA256_ENABLED = False

from umit.pm.core.i18n import _
from umit.pm.gui.core.views import UmitView

class HackBar(gtk.VBox):
    _url_encre = re.compile(r"[^A-Za-z0-9_.&?=/!~*()-]") # RFC 2396 section 2.3
    _url_decre = re.compile(r"%([0-9A-Fa-f]{2})")

    _rot13_table = string.maketrans(
        'nopqrstuvwxyzabcdefghijklmNOPQRSTUVWXYZABCDEFGHIJKLM',
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

    def __init__(self):
        super(HackBar, self).__init__(False, 2)

        self.text = gtk.TextView()
        self.text.set_wrap_mode(gtk.WRAP_WORD)
        self.text.modify_font(pango.FontDescription("mono"))

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.text)

        self.menubar = gtk.MenuBar()
        self.pack_start(self.menubar, False, False)
        self.pack_start(sw)

        self.__create_trans()
        self.__create_crypt()
        self.__create_encoding()
        self.__create_database()

    def __create_trans(self):
        root = gtk.Menu()

        action = gtk.Action(None, _('Transformation'), None,
                            gtk.STOCK_JUSTIFY_FILL)

        item = action.create_menu_item()
        item.set_submenu(root)

        self.menubar.append(item)

        lbls = (_('Upper'), _('Lower'))
        cbs = (self.__upper, self.__lower)

        for lbl, cb in zip(lbls, cbs):
            action = gtk.Action(None, lbl, None, gtk.STOCK_JUSTIFY_FILL)

            item = action.create_menu_item()
            action.connect('activate', cb)

            root.append(item)

    def __create_crypt(self):
        root = gtk.Menu()

        action = gtk.Action(None, _('Encryption'), None,
                            gtk.STOCK_DIALOG_AUTHENTICATION)

        item = action.create_menu_item()
        item.set_submenu(root)

        self.menubar.append(item)

        lbls = ('MD5', 'SHA-1', 'SHA-256', 'ROT13')
        cbs = (self.__crypt_md5, self.__crypt_sha1,
               self.__crypt_sha256, self.__crypt_rot13)

        for lbl, cb in zip(lbls, cbs):
            action = gtk.Action(None, lbl, None,
                                gtk.STOCK_DIALOG_AUTHENTICATION)

            item = action.create_menu_item()
            action.connect('activate', cb)

            if lbl == "SHA-256":
                item.set_sensitive(SHA256_ENABLED)

            root.append(item)

    def __create_encoding(self):
        root = gtk.Menu()

        action = gtk.Action(None, _('Encoding'), None, gtk.STOCK_CONVERT)

        item = action.create_menu_item()
        item.set_submenu(root)

        self.menubar.append(item)

        lbls = (_('Base64 Encode'), _('Base64 Decode'), _('URL Encode'),
                _('URL Decode'))
        cbs = (self.__enc_base64, self.__dec_base64, self.__enc_url,
               self.__dec_url)

        for lbl, cb in zip(lbls, cbs):
            action = gtk.Action(None, lbl, None, gtk.STOCK_CONVERT)

            item = action.create_menu_item()
            action.connect('activate', cb)

            root.append(item)

    def __create_database(self):
        root = gtk.Menu()

        action = gtk.Action(None, _('Database'), None, gtk.STOCK_INDEX)

        item = action.create_menu_item()
        item.set_submenu(root)

        self.menubar.append(item)

        lbls = (_('MySQL Encode'), _('MySQL Decode'), _('MsSQL Encode'),
                _('MsSQL Decode'))
        cbs = (self.__enc_my, self.__dec_my, self.__enc_ms, self.__dec_ms)

        for lbl, cb in zip(lbls, cbs):
            action = gtk.Action(None, lbl, None, gtk.STOCK_INDEX)

            item = action.create_menu_item()
            action.connect('activate', cb)

            root.append(item)

    def get_selection(self):
        if not self.text.get_buffer().get_selection_bounds():
            return None

        s, e = self.text.get_buffer().get_selection_bounds()
        return self.text.get_buffer().get_text(s, e, True)

    def set_selection(self, txt):
        buffer = self.text.get_buffer()
        s, e = buffer.get_selection_bounds()

        if s > e:
            s, e = e, s

        buffer.delete(s, e)
        buffer.insert_at_cursor(txt)

        e = buffer.get_iter_at_mark(buffer.get_insert())
        s = e.copy()
        s.backward_chars(len(txt))

        buffer.select_range(s, e)

    def text_getter(func):

        def get_text(*args):
            txt = args[0].get_selection()

            if not txt or txt == "":
                return False

            try:
                txt = func(args[0], txt)

                if txt:
                    args[0].set_selection(txt)
                    return True

                return False
            except Exception:
                return False

        return get_text

    @text_getter
    def __upper(self, txt):
        return txt.upper()

    @text_getter
    def __lower(self, txt):
        return txt.lower()

    @text_getter
    def __crypt_md5(self, txt):
        return md5(txt).hexdigest()

    @text_getter
    def __crypt_sha1(self, txt):
        return sha1(txt).hexdigest()

    @text_getter
    def __crypt_sha256(self, txt):
        try:
            return sha256(txt).hexdigest()
        except:
            return ""

    @text_getter
    def __crypt_rot13(self, txt):
        return string.translate(txt, HackBar._rot13_table)

    @text_getter
    def __enc_base64(self, txt):
        return base64.urlsafe_b64encode(txt)

    @text_getter
    def __dec_base64(self, txt):
        return base64.urlsafe_b64decode(txt)

    @text_getter
    def __enc_url(self, txt):
        return re.sub(HackBar._url_encre,
                      lambda m: "%%%02X" % ord(m.group(0)), txt)

    @text_getter
    def __dec_url(self, txt):
        txt = txt.replace("+", " ")
        return re.sub(HackBar._url_decre,
                      lambda m: chr(int(m.group(1), 16)), txt)

    @text_getter
    def __enc_my(self, txt):
        return ("CHAR%s" % map(ord, txt)).replace("[", "(").replace("]", ")")

    @text_getter
    def __dec_my(self, txt):
        return "".join(map(chr, map(int, txt.replace(" ", "")\
                                    [txt.index("(") + 1:-1].split(","))))

    @text_getter
    def __enc_ms(self, txt):
        return "".join (map (lambda x: "CHAR(%d)+" % ord (x), txt))[:-1]

    @text_getter
    def __dec_ms(self, txt):
        return "".join(map(chr, map(int, txt.replace(" ", "").\
                        replace("CHAR(", "").replace(")", "").split("+"))))


class HackTab(UmitView):
    icon_name = gtk.STOCK_CONVERT
    tab_position = gtk.POS_BOTTOM
    label_text = _('Hack Tab')
    name = 'HackTab'

    def create_ui(self):
        self._main_widget.add(HackBar())
        self._main_widget.show_all()
