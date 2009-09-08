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

import gtk
import pango
import gobject

class BaseText(gtk.TextView):
    __gtype_name__ = "BaseText"

    def __init__(self, parent):
        self.buffer = gtk.TextBuffer(parent.table)
        gtk.TextView.__init__(self, self.buffer)

        self._parent = parent
        self.modify_font(pango.FontDescription(parent.font))
        self.set_editable(False)

gobject.type_register(BaseText)

class OffsetText(BaseText):
    def __init__(self, parent):
        BaseText.__init__(self, parent)

        self.off_len = 1
        self.connect('button-press-event', self.__on_button_press)
        self.connect('size-request', self.__on_size_request)
        self.connect('realize', self.__on_realize)

        self.set_cursor_visible(False)

    def __on_button_press(self, widget, evt):
        return True

    def __on_realize(self, widget):
        self.modify_base(gtk.STATE_NORMAL, self.style.dark[gtk.STATE_NORMAL])

    def render(self, txt):
        self.buffer.set_text('')

        bpl = self._parent.bpl
        tot_lines = int(len(txt) / bpl)

        if len(txt) % bpl != 0:
            tot_lines += 1

        self.off_len = len(str(tot_lines)) + 1
        output = []

        for i in xrange(tot_lines):
            output.append(("%0" + str(self.off_len) + "d") % i)

        if output:
            self.buffer.insert_with_tags(
                self.buffer.get_end_iter(),
                "\n".join(output),
                self._parent.tag_offset
            )

    def __on_size_request(self, widget, alloc):
        ctx = self.get_pango_context()
        font = ctx.load_font(pango.FontDescription(self._parent.font))
        metric = font.get_metrics(ctx.get_language())

        w = pango.PIXELS(metric.get_approximate_char_width()) * (self.off_len + 1)
        w += 2

        if alloc.width < w:
            alloc.width = w

class AsciiText(BaseText):
    _printable = \
        "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%" \
        "&'()*+,-./:;<=>?@[\]^_`{|}~"

    def __init__(self, parent):
        BaseText.__init__(self, parent)
        self.connect('size-request', self.__on_size_request)

        self.prev_start = None
        self.prev_end = None

    def render(self, txt):
        self.buffer.set_text('')

        bpl = self._parent.bpl
        tot_lines = len(txt) / bpl

        if len(txt) % bpl != 0:
            tot_lines += 1

        output = []

        convert = lambda i: "".join(
            map(lambda x: (x in AsciiText._printable) and (x) or ('.'),
                list(i)))

        for i in xrange(tot_lines):
            to_fill = 0

            if i * bpl + bpl > len(txt):
                to_fill = (i * bpl) + bpl - len(txt)
                output.append(
                    convert(txt[i * bpl:])
                )
            else:
                output.append(
                    convert(txt[i * bpl:(i * bpl) + bpl])
                )

        if output:
            self.buffer.insert_with_tags(
                self.buffer.get_end_iter(),
                "\n".join(output),
                self._parent.tag_ascii
            )

    def __on_size_request(self, widget, alloc):
        ctx = self.get_pango_context()
        font = ctx.load_font(pango.FontDescription(self._parent.font))
        metric = font.get_metrics(ctx.get_language())

        w = pango.PIXELS(metric.get_approximate_char_width()) * self._parent.bpl
        w += 2

        if alloc.width < w:
            alloc.width = w

    def select_blocks(self, start=None, end=None):

        if self.prev_start and self.prev_end and \
           self.prev_start != self.prev_end:

            self.buffer.remove_tag(self._parent.tag_sec_sel, self.prev_start,
                                   self.prev_end)

        if not start and not end:
            return

        start_iter = self.buffer.get_iter_at_line(start / self._parent.bpl)
        start_iter.forward_chars(start % self._parent.bpl)

        end_iter = self.buffer.get_iter_at_line(end / self._parent.bpl)
        end_iter.forward_chars(end % self._parent.bpl)

        self.buffer.apply_tag(self._parent.tag_sec_sel, start_iter, end_iter)
        self.prev_start, self.prev_end = start_iter, end_iter


class HexText(BaseText):
    def __init__(self, parent):
        BaseText.__init__(self, parent)
        self.connect('size-request', self.__on_size_request)
        self.connect('realize', self.__on_realize)

        self.prev_start = None
        self.prev_end = None

    def __on_realize(self, widget):
        self.modify_base(gtk.STATE_NORMAL, self.style.mid[gtk.STATE_NORMAL])

    def render(self, txt):
        self.buffer.set_text('')

        bpl = self._parent.bpl
        tot_lines = int(len(txt) / bpl)

        if len(txt) % bpl != 0:
            tot_lines += 1

        output = []
        convert = lambda x: (len(x) == 1) and ("0%s" % x) or (x)

        for i in xrange(tot_lines):
            to_fill = 0

            if i * bpl + bpl > len(txt):
                to_fill = (i * bpl) + bpl - len(txt)
                output.append(
                    " ".join(map(lambda x: convert(str(hex(ord(x)))[2:]),
                                 txt[i * bpl:]))
                )
            else:
                output.append(
                    " ".join(map(lambda x: convert(str(hex(ord(x)))[2:]),
                                 txt[i * bpl:(i * bpl) + bpl]))
                )

        if output:
            self.buffer.insert_with_tags(
                self.buffer.get_end_iter(),
                "\n".join(output).upper(),
                self._parent.tag_hex
            )

    def __on_size_request(self, widget, alloc):
        ctx = self.get_pango_context()
        font = ctx.load_font(pango.FontDescription(self._parent.font))
        metric = font.get_metrics(ctx.get_language())

        w = pango.PIXELS(metric.get_approximate_char_width()) * \
                        (self._parent.bpl * 3 - 1)
        w += 2

        if alloc.width < w:
            alloc.width = w

    def select_blocks(self, start=None, end=None):

        if self.prev_start and self.prev_end and \
           self.prev_start != self.prev_end:

            self.buffer.remove_tag(self._parent.tag_sec_sel, self.prev_start,
                                   self.prev_end)

        if not start and not end:
            return

        start_iter = self.buffer.get_iter_at_line(start / self._parent.bpl)
        start_iter.forward_chars(3 * (start % self._parent.bpl))

        end_iter = self.buffer.get_iter_at_line(end / self._parent.bpl)
        end_iter.forward_chars(3 * (end % self._parent.bpl) - 1)

        self.buffer.apply_tag(self._parent.tag_sec_sel, start_iter, end_iter)
        self.prev_start, self.prev_end = start_iter, end_iter


class HexView(gtk.HBox):
    __gtype_name__ = "HexView"

    def __init__(self):
        gtk.HBox.__init__(self, False, 4)
        self.set_border_width(4)

        self.table = gtk.TextTagTable()
        self.tag_offset = gtk.TextTag('hex-o-view')       # offset view
        self.tag_hex = gtk.TextTag('hex-x-view')          # hex view
        self.tag_ascii = gtk.TextTag('hex-a-view')        # ascii view
        self.tag_sec_sel = gtk.TextTag('hex-s-selection') # secondary selection

        self.table.add(self.tag_offset)
        self.table.add(self.tag_hex)
        self.table.add(self.tag_ascii)
        self.table.add(self.tag_sec_sel)

        self._bpl = 16
        self._font = "Monospace 10"
        self._payload = ""

        vadj, hadj = gtk.Adjustment(), gtk.Adjustment()
        self.vscroll = gtk.VScrollbar(vadj)

        self.offset_text = OffsetText(self)
        self.hex_text = HexText(self)
        self.ascii_text = AsciiText(self)

        self.offset_text.set_scroll_adjustments(hadj, vadj)
        self.hex_text.set_scroll_adjustments(hadj, vadj)
        self.ascii_text.set_scroll_adjustments(hadj, vadj)

        self.hex_text.buffer.connect('mark-set', self.__on_hex_change)
        self.ascii_text.buffer.connect('mark-set', self.__on_ascii_change)

        self.hex_text.connect('populate-popup', self.__on_menu_popup)
        self.ascii_text.connect('populate-popup', self.__on_menu_popup)

        def scroll(widget):
            widget.set_size_request(-1, 80)
            frame = gtk.Frame()
            frame.set_shadow_type(gtk.SHADOW_IN)
            frame.add(widget)
            return frame

        self.pack_start(scroll(self.offset_text), False, False)
        self.pack_start(scroll(self.hex_text), False, False)
        self.pack_start(scroll(self.ascii_text), False, False)
        self.pack_end(self.vscroll, False, False)

    def do_realize(self):
        gtk.HBox.do_realize(self)

        # Offset view
        self.tag_offset.set_property('weight', pango.WEIGHT_BOLD)

        # Hex View
        self.tag_hex.set_property(
            'background-gdk',
            self.style.mid[gtk.STATE_NORMAL]
        )

        # Selection tags
        self.tag_sec_sel.set_property(
            'background-gdk',
            self.style.text_aa[gtk.STATE_NORMAL]
        )

    def __on_menu_popup(self, widget, menu):
        item = gtk.SeparatorMenuItem()
        item.show()

        menu.append(item)

        action = gtk.Action('', 'Copy from both', '', gtk.STOCK_COPY)
        item = action.create_menu_item()
        item.connect('activate', self.__on_copy_from_both)

        menu.append(item)

    def __on_copy_from_both(self, widget):
        if self.hex_text.buffer.get_selection_bounds():
            # Hex active

            start, end = self.hex_text.buffer.get_selection_bounds()
            txt = self.hex_text.buffer.get_text(start, end).replace("\n", " ")

            hex_s = filter(lambda x: len(x) == 2, txt.split(" "))
            ascii = map(lambda x: chr(int(x, 16)), hex_s)

            extend = self.bpl - len(hex_s) % self.bpl

            hex_s.extend(["  "] * extend)
            ascii.extend([" "] * extend)

            output = ""

            for i in xrange(len(hex_s) / self.bpl):
                output += "%s %s\n" % (
                    " ".join(hex_s[i * self.bpl:(i * self.bpl) + self.bpl]),
                    "".join(ascii[i * self.bpl:(i * self.bpl) + self.bpl])
                )

        elif self.ascii_text.buffer.get_selection_bounds():
            # Ascii active

            start, end = self.ascii_text.buffer.get_selection_bounds()
            ascii = list(
                self.ascii_text.buffer.get_text(start, end).replace("\n", "")
            )
            hex_s = map(lambda x: str(hex(ord(x)))[2:], ascii)

            extend = self.bpl - len(ascii) % self.bpl

            hex_s.extend(["  "] * extend)
            ascii.extend([" "] * extend)

            output = ""

            for i in xrange(len(hex_s) / self.bpl):
                output += "%s %s\n" % (
                    " ".join(hex_s[i * self.bpl:i * self.bpl + self.bpl]),
                    "".join(ascii[i * self.bpl:i * self.bpl + self.bpl])
                )

    def __on_hex_change(self, buffer, iter, mark):
        if not self.hex_text.buffer.get_selection_bounds():
            self.ascii_text.select_blocks() # Deselect
            return

        start, end = buffer.get_selection_bounds()

        if start.get_line() == end.get_line():
            tmp = buffer.get_iter_at_line(start.get_line())
            txt = buffer.get_text(tmp, start)
            s_off = len(filter(lambda x: x != '', txt.split(" ")))

            txt = buffer.get_text(start, end)
            e_off = len(filter(lambda x: len(x) == 2, txt.split(" ")))

            self.ascii_text.select_blocks(
                (self.bpl * start.get_line()) + s_off,
                (self.bpl * start.get_line()) + s_off + e_off
            )
        else:
            tmp = buffer.get_iter_at_line(start.get_line())
            txt = buffer.get_text(tmp, start)
            s_off = len(filter(lambda x: x != '', txt.split(" ")))

            tmp = buffer.get_iter_at_line(end.get_line())
            txt = buffer.get_text(tmp, end)
            e_off = len(filter(lambda x: len(x) == 2, txt.split(" ")))

            self.ascii_text.select_blocks(
                (self.bpl * start.get_line()) + s_off,
                (self.bpl * end.get_line()) + e_off
            )

    def __on_ascii_change(self, buffer, iter, mark):
        if not self.ascii_text.buffer.get_selection_bounds():
            self.hex_text.select_blocks() # Deselect
            return

        start, end = self.ascii_text.buffer.get_selection_bounds()
        self.hex_text.select_blocks(
            (self.bpl * start.get_line()) + start.get_line_index(),
            (self.bpl * end.get_line()) + end.get_line_index()
        )

    def select_block(self, offset, len, ascii=True):
        """
        Select a block of data in the HexView

        @param offset the offset byte
        @param len the lenght of selection
        @param ascii True to set primary selection on ASCII otherwise on HEX
        """

        start = offset
        end = offset + len

        # We need to add the \n characters one for each line
        start += start / self._bpl
        end += end / self._bpl

        if start > end:
            start, end = end, start

        if ascii:
            # We need to get a fucking iter!
            buffer = self.ascii_text.get_buffer()
            start_iter = buffer.get_iter_at_offset(start)
            end_iter   = buffer.get_iter_at_offset(end)

            buffer.select_range(end_iter, start_iter)

    def get_payload(self):
        return self._payload
    def set_payload(self, val):
        self._payload = val

        for view in (self.offset_text, self.hex_text, self.ascii_text):

            # Invalidate previous iters
            if hasattr(view, 'prev_start'):
                view.prev_start = None
            if hasattr(view, 'prev_end'):
                view.prev_end = None

            view.render(self._payload)

    def get_font(self):
        return self._font
    def modify_font(self, val):
        try:
            desc = pango.FontDescription(val)
            self._font = val

            for view in (self.offset_text, self.hex_text, self.ascii_text):
                view.modify_font(desc)
        except Exception:
            pass

    def get_bpl(self):
        return self._bpl
    def set_bpl(self, val):
        self._bpl = val

        # Redraw!
        self.payload = self.payload

    payload = property(get_payload, set_payload)
    font = property(get_font, modify_font)
    bpl = property(get_bpl, set_bpl)

gobject.type_register(HexView)

if __name__ == "__main__":
    w = gtk.Window()
    view = HexView()
    view.show_payload("Woo welcome this is a simple read/only"
                      " HexView widget for PacketManipulator")
    w.add(view)
    w.show_all()
    w.connect('delete-event', lambda *w: gtk.main_quit())
    gtk.main()
