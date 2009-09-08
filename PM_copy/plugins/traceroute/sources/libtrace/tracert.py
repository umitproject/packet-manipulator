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

import urllib
from umit.pm.core.logger import log

def get_my_ip():
    url = urllib.URLopener()
    resp = url.open('http://myip.dk')
    html = resp.read(256)

    end = html.find("</title>")
    start = html.find("address is: ") + 12

    return html[start:end].strip()

def generate_map(points):
    i = len(points) - 1
    last = None

    while i >= 0:
        if points[i][1] is not None:
            last = points[i][1]
        else:
            points[i] = (points[i][0], last)

        i -= 1

    i = 0
    last = None

    while i < len(points):
        if points[i][1] is not None:
            last = points[i][1]
        else:
            points[i][1] = (points[i][0], last)

        i += 1

    html = []

    for point in points:
        html.append("new GLatLng(%f, %f)" % (point[1][1], point[1][0]))

    head = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
<title>PacketManipulator: Traceroute</title>
<script src="http://maps.google.com/maps?file=api&amp;v=2&amp;key=ABQIAAAAQQRAsOk3uqvy3Hwwo4CclBTrVPfEE8Ms0qPwyRfPn-DOTlpaLBTvTHRCdf2V6KbzW7PZFYLT8wFD0A"
        type="text/javascript"></script>
<style type="text/css">
v\:* {behavior:url(#default#VML);}
html, body {width: 100%; height: 100%}
body {margin-top: 0px; margin-right: 0px; margin-left: 0px; margin-bottom: 0px}
</style>
<script type="text/javascript">
function initialize() {
  if (GBrowserIsCompatible()) {
    var map = new GMap2(document.getElementById("map_canvas"));
    map.setCenter(new GLatLng("""

    head += "%s,%s%s" % (points[0][1][1], points[0][1][0], "), 0);")
    head += "var polyline = new GPolyline(["
    head += ",".join(html)
    head += """], "#0000ff", 5);
		map.addOverlay(polyline);"""

    head += """
        map.addControl(new GSmallMapControl());
        map.addControl(new GMapTypeControl());

        function createMarker(point, info_text) {
          var marker = new GMarker(point, {});

          GEvent.addListener(marker, "click", function() {
            marker.openInfoWindowHtml(info_text);
          });

          return marker;
        }
    """

    for point in html:
        head += "map.addOverlay(createMarker(%s, \"%s\"));" % (point, points.pop(0)[0])

    head += """
        if (window.attachEvent) {
          window.attachEvent("onresize", function() {this.map.onResize()} );
        } else {
          window.addEventListener("resize", function() {this.map.onResize()} , false);
        }
    }
}
</script>
</head>

<body onload="initialize()" onunload="GUnload()">
<div id="map_canvas" style="width: 100%; height: 100%;"></div>
<div id="message">Traceroute for PacketManipulator</div>
</body>
</html>"""

    return head

def create_map(ans, locator):
    log.debug("Creating map")

    dct = ans.get_trace()

    if not dct.keys():
        return ""

    if not locator:
        return "<pre>Locator is not available.<br/>" \
               "Probably the geoip database is not present.</pre>"

    key = dct.keys()[0]
    routes = dct[key].items()
    routes.sort()

    ip = get_my_ip()
    last = locator.lon_lat(ip)

    points = []

    for k, (ip, is_ok) in routes:
        loc = locator.lon_lat(ip)

        if loc is None:
            loc = last
        else:
            last = loc

        points.append((ip, loc))

    return generate_map(points)
