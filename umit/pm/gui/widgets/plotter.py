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
import cairo
import pango
import gobject
import pangocairo

from umit.pm import backend
from umit.pm.core.atoms import defaultdict

from math import pi

class Plotter(gtk.DrawingArea):
    __gtype_name__ = "Plotter"

    def __init__(self, packet):
        self.colors = (
            gtk.gdk.color_parse('#FFFA99'),
            gtk.gdk.color_parse('#8DFF7F'),
            gtk.gdk.color_parse('#FFE3E5'),
            gtk.gdk.color_parse('#C797FF'),
            gtk.gdk.color_parse('#A0A0A0'),
            gtk.gdk.color_parse('#D6E8FF'),
            gtk.gdk.color_parse('#C2C2FF'),
        )

        self.packet = packet
        self.protocols = [] # (protocol, color)
        self.fields = {}

        self.hex_font = "Monospace 10"
        self.title_font = "Monospace 8"
        self.attr_font = "Monospace 8"

        super(Plotter, self).__init__()

    def do_size_request(self, req):
        w, h = self.get_requested_size()
        req.width = w; req.height = h

    def get_requested_size(self):
        # Get the requested size of the hex view part
        layout = self.create_pango_layout('FF')
        layout.set_font_description(pango.FontDescription(self.hex_font))

        atom_w, atom_h = layout.get_pixel_size()

        req_w = (atom_w + 4) * (16 + 1)
        req_h = (atom_h + 4) * (16 + 1)

        layout.set_font_description(pango.FontDescription(self.attr_font))
        layout.set_text('A')

        atom_w, atom_h = layout.get_pixel_size()

        fields = 0
        protos = [proto for proto in self.packet.get_protocols()]

        for proto in protos:
            for field in backend.get_proto_fields(proto):
                fields += 1

        protos = len(protos)

        req_w += 10 + (atom_w * 35) # 35 characters for attributes
        req_h = max(req_h, (fields + protos) * (atom_h + 4))

        return int(req_w), int(req_h)

    def draw_text(self, cr, layout, txt):
        cr.save()

        layout.set_text(txt)
        cr.show_layout(layout)

        cr.restore()

    def draw_boxed(self, cr, layout, txt, desc=None):
        cr.save()

        layout.set_text(txt)

        cr.show_layout(layout)

        w, h = layout.get_pixel_size()
        x, y = cr.get_current_point()

        cr.set_source_rgba(1, 0, 1, 0.3)
        cr.rectangle(x-2, y-2, w+4, h+4)
        cr.fill()

        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(x-2, y-2, w+4, h+4)
        cr.stroke()

        cr.restore()

        return w+4, h+4

    def __get_color(self, name):
        return self.colors[hash(name) % len(self.colors)]

    def __cairo_draw(self, cr):
        cr.save()

        self.fields = {}
        self.protocols = []

        for protocol in self.packet.get_protocols():
            self.protocols.append(
                    (protocol,
                     self.__get_color(backend.get_proto_name(protocol)))
            )

        self.draw_left(cr)
        self.draw_payload(cr)

        cr.restore()

    def export_to(self, fname):
        area = self.allocation
        WIDTH, HEIGHT = area.width, area.height

        if '.ps' in fname:
            surface = cairo.PSSurface(fname, WIDTH, HEIGHT)
            cr = pangocairo.CairoContext(cairo.Context(surface))

            self.__cairo_draw(cr)

            surface.flush()
        elif '.pdf' in fname:
            surface = cairo.PDFSurface(fname, WIDTH, HEIGHT)
            cr = pangocairo.CairoContext(cairo.Context(surface))

            self.__cairo_draw(cr)

            surface.flush()
        else:
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
            cr = pangocairo.CairoContext(cairo.Context(surface))

            self.__cairo_draw(cr)

            surface.write_to_png(fname)

    def do_expose_event(self, evt):
        cr = self.window.cairo_create()
        self.__cairo_draw(cr)
        return True

    def draw_line(self, cr, proto, fieldname):
        points = self.fields[(proto, fieldname)]

        if len(points) < 2:
            return

        cr.save()
        cr.set_line_width(1)

        old_x, old_y = cr.get_current_point()

        sx, sy = points[0]
        ex, ey = points[1]

        mx, my = (ex + sx) / 2, (ey + sy) / 2

        self.set_color(cr, self.__get_color(fieldname), 0.5, 0.7)

        cr.move_to(sx, sy)
        cr.curve_to(ex, sy, ex, my, ex, ey)
        cr.stroke()

        # Draw the arrow
        self.draw_arrow(cr, ex, ey)

        cr.stroke()

        cr.restore()

        cr.move_to(old_x, old_y)

    def draw_arrow(self, cr, x, y):
        cr.move_to(x, y - 6)
        cr.rel_line_to(4, 6)
        cr.rel_line_to(-8, 0)
        cr.close_path ()

        cr.fill()

    def draw_payload(self, cr):
        payload = self.packet.get_raw()

        layout = self.create_pango_layout('')
        layout.set_font_description(pango.FontDescription(self.hex_font))

        layout.set_text("FF")
        atom_x, atom_y = layout.get_pixel_size()

        atom_x += atom_x / 2.0
        atom_y += atom_y / 2.0

        start_x = self.allocation.width - (atom_x * 16) - 10

        cr.move_to(start_x, 4)

        # We should have space to place 16 bytes in hex

        dct = defaultdict(list)

        protocol_idx = 0

        for protocol, color in self.protocols:

            for field in backend.get_proto_fields(protocol):

                if not backend.is_showable_field(field, self.packet):
                    continue

                start = backend.get_field_offset(self.packet, protocol, field)
                end = backend.get_field_size(protocol, field)

                start /= 8

                dct[start].append((end, field))

            # Now we have the dict so we have to transform to
            # a sorted list

            lst = dct.items()
            lst.sort()

            tot_w = 0
            tot_h = 0

            for offset, child_list in lst:

                # We have also a child list to iterate
                size = 0

                if len(child_list) == 1 and child_list[0][0] == 0:
                    continue
                else:
                    for end, field in child_list:
                        size += end

                    size /= 8

                current_field = child_list[-1][1]
                field_name = backend.get_field_name(current_field)
                fill_color = self.__get_color(field_name)
                border_color = color

                line_x = offset % 16
                line_y = offset / 16

                txt = payload[offset:offset + size]

                if size + line_x > 16:
                    start = 16 - line_x

                    top_right = txt[0:start]

                    top_right = " ".join(["%02X" % ord(x) for x in top_right])
                    layout.set_text(top_right)

                    cr.move_to(start_x + (line_x * atom_x),
                               (line_y + protocol_idx) * atom_y + 4)

                    # Here we should write <==
                    self.draw_box(cr, layout, fill=fill_color,
                                  border=border_color, right=False)

                    w, h = 0, 0
                    txt = txt[start:]
                    lines = (len(txt) / 16) + 1

                    for i in xrange(lines):
                        right, left = False, False

                        if len(txt) > 16:
                            # here ===
                            part = txt[i * 16:(i * 16) + 16]
                        else:
                            right = True
                            part = txt[i * 16:]

                        if i == lines - 1:
                            right = True

                        cr.move_to(start_x,
                                   (line_y + protocol_idx + i + 1) * atom_y + 4)

                        part = " ".join(["%02X" % ord(x) for x in part])
                        layout.set_text(part)


                        w, h = self.draw_box(cr, layout, fill=fill_color,
                                             border=border_color,
                                             right=right, left=left)

                    # End point
                    self.fields[(protocol, field_name)].append(
                            (start_x + (w / 2.0),
                            (line_y + protocol_idx + lines + 1) * atom_y + 8))
                else:
                    txt = " ".join(["%02X" % ord(x) for x in txt])
                    layout.set_text(txt)

                    cr.move_to(start_x + (line_x * atom_x),
                               (line_y + protocol_idx) * atom_y + 4)

                    w, h = self.draw_box(cr, layout, fill=fill_color,
                                         border=border_color)

                    tot_w += w + 4
                    tot_h = max(tot_h, h)

                    # End point
                    self.fields[(protocol, field_name)].append(
                                (start_x + (line_x * atom_x) + (w / 2.0),
                                (tot_h + (protocol_idx + line_y) * atom_y + 8)))

                self.draw_line(cr, protocol, field_name)

            cr.rel_move_to(0, tot_h + 4)

            dct = defaultdict(list)

            protocol_idx += 1

    def draw_left(self, cr):
        layout = self.create_pango_layout('')
        layout.set_font_description(pango.FontDescription(self.title_font))

        attr_layout = self.create_pango_layout('')
        attr_layout.set_font_description(pango.FontDescription(self.attr_font))

        cr.move_to(4, 4)

        for protocol, color in self.protocols:
            name = backend.get_proto_name(protocol)
            layout.set_text(name)

            w, h = self.draw_box(cr, layout, fill=color)

            cr.rel_move_to(0, h + 4)

            x, y = cr.get_current_point()
            cr.move_to(x + 10, y)

            for field in backend.get_proto_fields(protocol):

                if not backend.is_showable_field(field, self.packet):
                    continue

                name = backend.get_field_name(field)
                value = str(backend.get_field_value_repr(protocol, field))

                text = '%s: %s' % (name, value)

                if len(text) > 35:
                    text = text[0:32] + "..."

                attr_layout.set_text(text)

                f_w, f_h = self.draw_text(cr, attr_layout)

                # Start point
                x, y = cr.get_current_point()
                self.fields[(protocol, name)] = [(x + f_w + 4, y + (f_h / 2.0))]

                cr.rel_move_to(0, f_h)

            cr.rel_move_to(-10, 10)

    def draw_text(self, cr, layout):
        cr.show_layout(layout)
        return layout.get_pixel_size()

    def set_color(self, cr, color, offset=0.05, rgba=1.0):
        cr.set_source_rgba(float(color.red) / 65535 - offset,
                          float(color.green) / 65535 - offset,
                          float(color.blue) / 65535 - offset, rgba)

    def draw_box(self, cr, layout, fill=None, border=None, bottom=True, \
                 top=True, right=True, left=True):

        w, h = layout.get_pixel_size()
        x, y = cr.get_current_point()

        if fill:
            cr.save()

            self.set_color(cr, fill)
            cr.rectangle(x, y, w + 4, h + 4)
            cr.fill()

            cr.restore()

        cr.save()

        if border:
            self.set_color(cr, border)
            cr.set_line_width(2)
        else:
            cr.set_source_rgb(0, 0, 0)

        if top:
            cr.move_to(x, y)
            cr.line_to(x + w + 4, y)
            cr.stroke()

        if bottom:
            cr.move_to(x, y + h + 4)
            cr.line_to(x + w + 4, y + h + 4)
            cr.stroke()

        if right:
            cr.move_to(x + w + 4, y)
            cr.line_to(x + w + 4, y + h + 4)
            cr.stroke()

        if left:
            cr.move_to(x, y)
            cr.line_to(x, y + h + 4)
            cr.stroke()

        cr.restore()

        cr.move_to(x + 2, y + 2)
        cr.show_layout(layout)

        cr.move_to(x, y)

        return w+4, h+4

gobject.type_register(Plotter)

if __name__ == "__main__":
    packet = backend.rdpcap("flow.pcap")[22]

    w = gtk.Window()
    w.add(Plotter(backend.MetaPacket(packet)))
    w.show_all()

    gtk.main()
