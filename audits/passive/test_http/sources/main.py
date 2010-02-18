#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2010 Adriano Monteiro Marques
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
Test HTTP dissector against file extraction

>>> from umit.pm.core.auditutils import audit_unittest
>>> audit_unittest('-f ethernet,ip,tcp,http,test_http', 'http_with_jpegs.pcap')
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive']
 -> get [['/', 'HTTP/1.1']]
 -> host ['10.1.1.1']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /
---
dissector.http.headers :
 -> accept-ranges ['bytes']
 -> connection ['close']
 -> content-length [160]
 -> content-type ['text/html; charset=ISO-8859-1']
 -> date ['Sat, 20 Nov 2004 10:21:06 GMT']
 -> etag ['"46eed-a0-800ce680"']
 -> http/1.1 [['200', 'OK']]
 -> last-modified ['Mon, 08 Mar 2004 20:27:54 GMT']
 -> server ['Apache/2.0.40 (Red Hat Linux)']
dissector.http.is_request False
dissector.http.is_response True
dissector.http.response 299f212f6e8dda731633b321fb6c4aec
dissector.http.response_protocol 1.1
dissector.http.response_status ['200', 'OK']
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive']
 -> content-length [433]
 -> content-type ['application/vnd.xacp']
 -> host ['ins1.opera.com']
 -> post [['/scripts/cms/xcms.asp', 'HTTP/1.1']]
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request dddfc089bd7a9e1c143022af40c44119
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri POST /scripts/cms/xcms.asp
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive, TE']
 -> get [['/Websidan/index.html', 'HTTP/1.1']]
 -> host ['10.1.1.1']
 -> referer ['http://10.1.1.1/']
 -> te ['deflate, gzip, chunked, identity, trailers']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /Websidan/index.html
---
dissector.http.headers :
 -> accept-ranges ['bytes']
 -> connection ['close']
 -> content-length [4323]
 -> content-type ['text/html; charset=ISO-8859-1']
 -> date ['Sat, 20 Nov 2004 10:21:07 GMT']
 -> etag ['"4abce-10e3-f6736fc0"']
 -> http/1.1 [['200', 'OK']]
 -> last-modified ['Sun, 29 Aug 2004 19:29:11 GMT']
 -> server ['Apache/2.0.40 (Red Hat Linux)']
dissector.http.is_request False
dissector.http.is_response True
dissector.http.response e4037be6b040aa6c9f0f409a6ca2aa45
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive, TE']
 -> get [['/Websidan/images/bg2.jpg', 'HTTP/1.1']]
 -> host ['10.1.1.1']
 -> referer ['http://10.1.1.1/Websidan/index.html']
 -> te ['deflate, gzip, chunked, identity, trailers']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /Websidan/images/bg2.jpg
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive, TE']
 -> get [['/Websidan/images/sydney.jpg', 'HTTP/1.1']]
 -> host ['10.1.1.1']
 -> referer ['http://10.1.1.1/Websidan/index.html']
 -> te ['deflate, gzip, chunked, identity, trailers']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /Websidan/images/sydney.jpg
---
dissector.http.headers :
 -> accept-ranges ['bytes']
 -> connection ['close']
 -> content-length [8281]
 -> content-type ['image/jpeg']
 -> date ['Sat, 20 Nov 2004 10:21:07 GMT']
 -> etag ['"46a4f-2059-5e467400"']
 -> http/1.1 [['200', 'OK']]
 -> last-modified ['Fri, 12 Jan 2001 05:00:00 GMT']
 -> server ['Apache/2.0.40 (Red Hat Linux)']
 -> x-pad ['avoid browser bug']
dissector.http.is_request False
dissector.http.is_response True
dissector.http.response ba1a813191165661b6cc5ef4344141c2
---
dissector.http.headers :
 -> accept-ranges ['bytes']
 -> connection ['close']
 -> content-length [9045]
 -> content-type ['image/jpeg']
 -> date ['Sat, 20 Nov 2004 10:21:07 GMT']
 -> etag ['"46a51-2355-d5a3f400"']
 -> http/1.1 [['200', 'OK']]
 -> last-modified ['Tue, 16 Jan 2001 05:00:00 GMT']
 -> server ['Apache/2.0.40 (Red Hat Linux)']
 -> x-pad ['avoid browser bug']
dissector.http.is_request False
dissector.http.is_response True
dissector.http.response f5d0c27ca554a8564e0ae1edd3ea002b
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive']
 -> cookie ['opera1=_4197c290,,126885^76592&127709^162766_; ACID=ee440010568883680002!; BASE=I9PbXsuDOePjSe2vKrrCSFCkbS4bJ4cuPcmErx85XsxxbLWN57hTMkwaoEGwJcbgAeiU6I3kLpaOB9FsfHZRMbi4E+6ANWpiTWCVj43x54Jamu4nxtXcghhEAMTGzIYIPsXQOttbEwPBD4EfFavQNSwBma85qhmudMAPtwj9bGZkrvYVvJh1IGOe769w/6tbmY0pHbrzlazeGlr+9wgQ2l1KAb+7+g06VQm30/O1HiiJ0oDPxRWVBNEJcGuH3rDtA405LpbFoxdVzqX8DK9Jgd7NZUJn6pGi0mZNEbfUN5jP82cZjapg5yw/Ae2r4Wcbtjas+w41VVm13apJtqT3cm1EkXnfoWkeYr07Kw4Bc6fY6ov/zNBWIHVtwfej6QaB8JD38YnFrBpHtoaD3m24SlXEYlhaNi9uth8DrfxdnQA/hVqqYCyW66F5sFP+ks79IK3o+KOui1fVBDssNcvfCND+a8LJ9wwIjEzmkHQ2bBIE7pcfO7GllXeqJwLRUPQ2Ccs/a7Z0jmdXKNC+Z9GIUaNyWKwvFQRSa1b5yMFRNGbCbIaQn5BHpWq4yN7JY1UifxjsNQvv8hXHPezOK/OolqE+k2oY9vUK6iVhJIcDDmSaPGJNf8KUsZxUskthDOzFfR0AFqLagTv3HWa14Tv++Up9kEmoP2pOObxY4rQWa95IEWDN88r41es86cnk0+Fkh8eY8URccZwFsrw4+FecKmqAtoGlEGhC9RCfN72oW4ATAP+SZsCoayViCJBuRdgXoeIij34w/wJgAIkcWTri+suR6vk27loQSeXJrkHJ5TINJnuV4CJw9Hfw8N3kb8jrT89X2FEdTsjFxyPj476AYTSU7luDDTIwlPP+S6I8VUGhotFELuHmZ/bNs4hHDDQesJYHoL7C0jmDkj3Qxua4d6Za6cxjIzTd0o6yVP6jeJWEsuIQ9sxzKrxWG5Ngd6jSLEQNX1xRM+E/EM7xmZEaAJdY98kKdxnVM1qk67DIhy29ZG8xYF1SfUtkqRTECV7tYy6WImFo+CPIHPTmpdwLHb38Kmj+7fKJI2GyjMr/mX0jww/ySaSKFQLw2APgKDYhhQ1kPOsgmsnmVqhhEDCwZ3R2CGMRE6ZSuzN7BLvBZpvcRNMiqRtyQwTfBORHP92eGyI2pUgMISxfZYfS2UCVtjKMAdBkl2lZPg71KKUiYlGhui1owWh4/AT/67cgJQcFuX/1MRbiiDZtjg5fuqlHNJjcWnYqFYYLOzWm+nSl47+2o+FEc38Q+uDDBaXVQQ5afYoLbFQ+axx+Ry99y2xnt+KaV2VrDgoIE4KgUN8wTgg0aD3ksAXFQtrnS+3R2/XWs6MxfuXXm3vRYVP/KqomT3av1lvxHDKmDF1KIbxrZgk/bPOtjNJvJNv1VGGNc7lXOyb9QIO3nNS0JkiogRYFuHUN9mTlxF5O5Q7cVJwIyZmQeenOG+k2a+pEu2lV/sXns0TCHJCfRoNFn5Xi9ugUKA36J8O4al71cLrQMClzYgFuPJ2xqn6Ukaih/RmD6X7o2bkw9Kr18jK0SspdbQlzfYjNsVGsTGWOX5MFmjn5foLuXg7BQNMSxy5WjKyCa/zAHGdFb0ju2Bv/pug9wmlVZOapWdmVBZM+ZjgcFezND9x3Q0C!; ROLL=31xDrGN5IimxKkJ51kc5Cx4G7qMgPtReMWYbRmrJuOY1K7T0qekbO3O4PBZKI/JVLaqdFAyPtYSbjo3WMAAeIqfFtCRWt/xKVPbo/EOHQah6/PQnwjFfXecQD+xHLgat+JBSLn+poF57xWdsYjdmaMqI1YfjU7xOIgQL+sklB1t3kGtcPaEE07NoKZnOW5ac3ml8vMH9ZZuYpMIPB8wxrYWVAfvwoy1oi7AoQsho/ZO6X3SxKTFyIXviy62QHGC+cYrI5y3b+20HxMb4+onw+vjDUiL436A!']
 -> cookie2 ['$Version=1']
 -> get [['/site=126885/bnum=opera1/bins=1/opid=10030285/ver=711/dst=Win_700', 'HTTP/1.1']]
 -> host ['opera1-servedby.advertising.com']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /site=126885/bnum=opera1/bins=1/opid=10030285/ver=711/dst=Win_700
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive']
 -> cookie ['opera2=_4197c290,,126885^76592&127709^162766_; ACID=ee440010568883680002!; BASE=I9PbXsuDOePjSe2vKrrCSFCkbS4bJ4cuPcmErx85XsxxbLWN57hTMkwaoEGwJcbgAeiU6I3kLpaOB9FsfHZRMbi4E+6ANWpiTWCVj43x54Jamu4nxtXcghhEAMTGzIYIPsXQOttbEwPBD4EfFavQNSwBma85qhmudMAPtwj9bGZkrvYVvJh1IGOe769w/6tbmY0pHbrzlazeGlr+9wgQ2l1KAb+7+g06VQm30/O1HiiJ0oDPxRWVBNEJcGuH3rDtA405LpbFoxdVzqX8DK9Jgd7NZUJn6pGi0mZNEbfUN5jP82cZjapg5yw/Ae2r4Wcbtjas+w41VVm13apJtqT3cm1EkXnfoWkeYr07Kw4Bc6fY6ov/zNBWIHVtwfej6QaB8JD38YnFrBpHtoaD3m24SlXEYlhaNi9uth8DrfxdnQA/hVqqYCyW66F5sFP+ks79IK3o+KOui1fVBDssNcvfCND+a8LJ9wwIjEzmkHQ2bBIE7pcfO7GllXeqJwLRUPQ2Ccs/a7Z0jmdXKNC+Z9GIUaNyWKwvFQRSa1b5yMFRNGbCbIaQn5BHpWq4yN7JY1UifxjsNQvv8hXHPezOK/OolqE+k2oY9vUK6iVhJIcDDmSaPGJNf8KUsZxUskthDOzFfR0AFqLagTv3HWa14Tv++Up9kEmoP2pOObxY4rQWa95IEWDN88r41es86cnk0+Fkh8eY8URccZwFsrw4+FecKmqAtoGlEGhC9RCfN72oW4ATAP+SZsCoayViCJBuRdgXoeIij34w/wJgAIkcWTri+suR6vk27loQSeXJrkHJ5TINJnuV4CJw9Hfw8N3kb8jrT89X2FEdTsjFxyPj476AYTSU7luDDTIwlPP+S6I8VUGhotFELuHmZ/bNs4hHDDQesJYHoL7C0jmDkj3Qxua4d6Za6cxjIzTd0o6yVP6jeJWEsuIQ9sxzKrxWG5Ngd6jSLEQNX1xRM+E/EM7xmZEaAJdY98kKdxnVM1qk67DIhy29ZG8xYF1SfUtkqRTECV7tYy6WImFo+CPIHPTmpdwLHb38Kmj+7fKJI2GyjMr/mX0jww/ySaSKFQLw2APgKDYhhQ1kPOsgmsnmVqhhEDCwZ3R2CGMRE6ZSuzN7BLvBZpvcRNMiqRtyQwTfBORHP92eGyI2pUgMISxfZYfS2UCVtjKMAdBkl2lZPg71KKUiYlGhui1owWh4/AT/67cgJQcFuX/1MRbiiDZtjg5fuqlHNJjcWnYqFYYLOzWm+nSl47+2o+FEc38Q+uDDBaXVQQ5afYoLbFQ+axx+Ry99y2xnt+KaV2VrDgoIE4KgUN8wTgg0aD3ksAXFQtrnS+3R2/XWs6MxfuXXm3vRYVP/KqomT3av1lvxHDKmDF1KIbxrZgk/bPOtjNJvJNv1VGGNc7lXOyb9QIO3nNS0JkiogRYFuHUN9mTlxF5O5Q7cVJwIyZmQeenOG+k2a+pEu2lV/sXns0TCHJCfRoNFn5Xi9ugUKA36J8O4al71cLrQMClzYgFuPJ2xqn6Ukaih/RmD6X7o2bkw9Kr18jK0SspdbQlzfYjNsVGsTGWOX5MFmjn5foLuXg7BQNMSxy5WjKyCa/zAHGdFb0ju2Bv/pug9wmlVZOapWdmVBZM+ZjgcFezND9x3Q0C!; ROLL=31xDrGN5IimxKkJ51kc5Cx4G7qMgPtReMWYbRmrJuOY1K7T0qekbO3O4PBZKI/JVLaqdFAyPtYSbjo3WMAAeIqfFtCRWt/xKVPbo/EOHQah6/PQnwjFfXecQD+xHLgat+JBSLn+poF57xWdsYjdmaMqI1YfjU7xOIgQL+sklB1t3kGtcPaEE07NoKZnOW5ac3ml8vMH9ZZuYpMIPB8wxrYWVAfvwoy1oi7AoQsho/ZO6X3SxKTFyIXviy62QHGC+cYrI5y3b+20HxMb4+onw+vjDUiL436A!']
 -> cookie2 ['$Version=1']
 -> get [['/site=126885/bnum=opera2/bins=1/opid=10030867/ver=711/dst=Win_700', 'HTTP/1.1']]
 -> host ['opera2-servedby.advertising.com']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /site=126885/bnum=opera2/bins=1/opid=10030867/ver=711/dst=Win_700
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive']
 -> cookie ['opera3=_4197c291,,126885^76592&127709^162766_; ACID=ee440010568883680002!; BASE=I9PbXsuDOePjSe2vKrrCSFCkbS4bJ4cuPcmErx85XsxxbLWN57hTMkwaoEGwJcbgAeiU6I3kLpaOB9FsfHZRMbi4E+6ANWpiTWCVj43x54Jamu4nxtXcghhEAMTGzIYIPsXQOttbEwPBD4EfFavQNSwBma85qhmudMAPtwj9bGZkrvYVvJh1IGOe769w/6tbmY0pHbrzlazeGlr+9wgQ2l1KAb+7+g06VQm30/O1HiiJ0oDPxRWVBNEJcGuH3rDtA405LpbFoxdVzqX8DK9Jgd7NZUJn6pGi0mZNEbfUN5jP82cZjapg5yw/Ae2r4Wcbtjas+w41VVm13apJtqT3cm1EkXnfoWkeYr07Kw4Bc6fY6ov/zNBWIHVtwfej6QaB8JD38YnFrBpHtoaD3m24SlXEYlhaNi9uth8DrfxdnQA/hVqqYCyW66F5sFP+ks79IK3o+KOui1fVBDssNcvfCND+a8LJ9wwIjEzmkHQ2bBIE7pcfO7GllXeqJwLRUPQ2Ccs/a7Z0jmdXKNC+Z9GIUaNyWKwvFQRSa1b5yMFRNGbCbIaQn5BHpWq4yN7JY1UifxjsNQvv8hXHPezOK/OolqE+k2oY9vUK6iVhJIcDDmSaPGJNf8KUsZxUskthDOzFfR0AFqLagTv3HWa14Tv++Up9kEmoP2pOObxY4rQWa95IEWDN88r41es86cnk0+Fkh8eY8URccZwFsrw4+FecKmqAtoGlEGhC9RCfN72oW4ATAP+SZsCoayViCJBuRdgXoeIij34w/wJgAIkcWTri+suR6vk27loQSeXJrkHJ5TINJnuV4CJw9Hfw8N3kb8jrT89X2FEdTsjFxyPj476AYTSU7luDDTIwlPP+S6I8VUGhotFELuHmZ/bNs4hHDDQesJYHoL7C0jmDkj3Qxua4d6Za6cxjIzTd0o6yVP6jeJWEsuIQ9sxzKrxWG5Ngd6jSLEQNX1xRM+E/EM7xmZEaAJdY98kKdxnVM1qk67DIhy29ZG8xYF1SfUtkqRTECV7tYy6WImFo+CPIHPTmpdwLHb38Kmj+7fKJI2GyjMr/mX0jww/ySaSKFQLw2APgKDYhhQ1kPOsgmsnmVqhhEDCwZ3R2CGMRE6ZSuzN7BLvBZpvcRNMiqRtyQwTfBORHP92eGyI2pUgMISxfZYfS2UCVtjKMAdBkl2lZPg71KKUiYlGhui1owWh4/AT/67cgJQcFuX/1MRbiiDZtjg5fuqlHNJjcWnYqFYYLOzWm+nSl47+2o+FEc38Q+uDDBaXVQQ5afYoLbFQ+axx+Ry99y2xnt+KaV2VrDgoIE4KgUN8wTgg0aD3ksAXFQtrnS+3R2/XWs6MxfuXXm3vRYVP/KqomT3av1lvxHDKmDF1KIbxrZgk/bPOtjNJvJNv1VGGNc7lXOyb9QIO3nNS0JkiogRYFuHUN9mTlxF5O5Q7cVJwIyZmQeenOG+k2a+pEu2lV/sXns0TCHJCfRoNFn5Xi9ugUKA36J8O4al71cLrQMClzYgFuPJ2xqn6Ukaih/RmD6X7o2bkw9Kr18jK0SspdbQlzfYjNsVGsTGWOX5MFmjn5foLuXg7BQNMSxy5WjKyCa/zAHGdFb0ju2Bv/pug9wmlVZOapWdmVBZM+ZjgcFezND9x3Q0C!; ROLL=31xDrGN5IimxKkJ51kc5Cx4G7qMgPtReMWYbRmrJuOY1K7T0qekbO3O4PBZKI/JVLaqdFAyPtYSbjo3WMAAeIqfFtCRWt/xKVPbo/EOHQah6/PQnwjFfXecQD+xHLgat+JBSLn+poF57xWdsYjdmaMqI1YfjU7xOIgQL+sklB1t3kGtcPaEE07NoKZnOW5ac3ml8vMH9ZZuYpMIPB8wxrYWVAfvwoy1oi7AoQsho/ZO6X3SxKTFyIXviy62QHGC+cYrI5y3b+20HxMb4+onw+vjDUiL436A!']
 -> cookie2 ['$Version=1']
 -> get [['/site=126885/bnum=opera3/bins=1/opid=10032112/ver=711/dst=Win_700', 'HTTP/1.1']]
 -> host ['opera3-servedby.advertising.com']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /site=126885/bnum=opera3/bins=1/opid=10032112/ver=711/dst=Win_700
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive']
 -> cookie ['opera4=_4197c291,,126885^76592&127709^162766_; ACID=ee440010568883680002!; BASE=I9PbXsuDOePjSe2vKrrCSFCkbS4bJ4cuPcmErx85XsxxbLWN57hTMkwaoEGwJcbgAeiU6I3kLpaOB9FsfHZRMbi4E+6ANWpiTWCVj43x54Jamu4nxtXcghhEAMTGzIYIPsXQOttbEwPBD4EfFavQNSwBma85qhmudMAPtwj9bGZkrvYVvJh1IGOe769w/6tbmY0pHbrzlazeGlr+9wgQ2l1KAb+7+g06VQm30/O1HiiJ0oDPxRWVBNEJcGuH3rDtA405LpbFoxdVzqX8DK9Jgd7NZUJn6pGi0mZNEbfUN5jP82cZjapg5yw/Ae2r4Wcbtjas+w41VVm13apJtqT3cm1EkXnfoWkeYr07Kw4Bc6fY6ov/zNBWIHVtwfej6QaB8JD38YnFrBpHtoaD3m24SlXEYlhaNi9uth8DrfxdnQA/hVqqYCyW66F5sFP+ks79IK3o+KOui1fVBDssNcvfCND+a8LJ9wwIjEzmkHQ2bBIE7pcfO7GllXeqJwLRUPQ2Ccs/a7Z0jmdXKNC+Z9GIUaNyWKwvFQRSa1b5yMFRNGbCbIaQn5BHpWq4yN7JY1UifxjsNQvv8hXHPezOK/OolqE+k2oY9vUK6iVhJIcDDmSaPGJNf8KUsZxUskthDOzFfR0AFqLagTv3HWa14Tv++Up9kEmoP2pOObxY4rQWa95IEWDN88r41es86cnk0+Fkh8eY8URccZwFsrw4+FecKmqAtoGlEGhC9RCfN72oW4ATAP+SZsCoayViCJBuRdgXoeIij34w/wJgAIkcWTri+suR6vk27loQSeXJrkHJ5TINJnuV4CJw9Hfw8N3kb8jrT89X2FEdTsjFxyPj476AYTSU7luDDTIwlPP+S6I8VUGhotFELuHmZ/bNs4hHDDQesJYHoL7C0jmDkj3Qxua4d6Za6cxjIzTd0o6yVP6jeJWEsuIQ9sxzKrxWG5Ngd6jSLEQNX1xRM+E/EM7xmZEaAJdY98kKdxnVM1qk67DIhy29ZG8xYF1SfUtkqRTECV7tYy6WImFo+CPIHPTmpdwLHb38Kmj+7fKJI2GyjMr/mX0jww/ySaSKFQLw2APgKDYhhQ1kPOsgmsnmVqhhEDCwZ3R2CGMRE6ZSuzN7BLvBZpvcRNMiqRtyQwTfBORHP92eGyI2pUgMISxfZYfS2UCVtjKMAdBkl2lZPg71KKUiYlGhui1owWh4/AT/67cgJQcFuX/1MRbiiDZtjg5fuqlHNJjcWnYqFYYLOzWm+nSl47+2o+FEc38Q+uDDBaXVQQ5afYoLbFQ+axx+Ry99y2xnt+KaV2VrDgoIE4KgUN8wTgg0aD3ksAXFQtrnS+3R2/XWs6MxfuXXm3vRYVP/KqomT3av1lvxHDKmDF1KIbxrZgk/bPOtjNJvJNv1VGGNc7lXOyb9QIO3nNS0JkiogRYFuHUN9mTlxF5O5Q7cVJwIyZmQeenOG+k2a+pEu2lV/sXns0TCHJCfRoNFn5Xi9ugUKA36J8O4al71cLrQMClzYgFuPJ2xqn6Ukaih/RmD6X7o2bkw9Kr18jK0SspdbQlzfYjNsVGsTGWOX5MFmjn5foLuXg7BQNMSxy5WjKyCa/zAHGdFb0ju2Bv/pug9wmlVZOapWdmVBZM+ZjgcFezND9x3Q0C!; ROLL=31xDrGN5IimxKkJ51kc5Cx4G7qMgPtReMWYbRmrJuOY1K7T0qekbO3O4PBZKI/JVLaqdFAyPtYSbjo3WMAAeIqfFtCRWt/xKVPbo/EOHQah6/PQnwjFfXecQD+xHLgat+JBSLn+poF57xWdsYjdmaMqI1YfjU7xOIgQL+sklB1t3kGtcPaEE07NoKZnOW5ac3ml8vMH9ZZuYpMIPB8wxrYWVAfvwoy1oi7AoQsho/ZO6X3SxKTFyIXviy62QHGC+cYrI5y3b+20HxMb4+onw+vjDUiL436A!']
 -> cookie2 ['$Version=1']
 -> get [['/site=126885/bnum=opera4/bins=1/opid=10003005/ver=711/dst=Win_700', 'HTTP/1.1']]
 -> host ['opera4-servedby.advertising.com']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /site=126885/bnum=opera4/bins=1/opid=10003005/ver=711/dst=Win_700
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive, TE']
 -> cookie ['opera1=_419e70fb,,126885^76592&127709^162763_; ACID=ee440010568883680002!; BASE=rf4aU+eDk32GTgLuc8W+tMhzq1tXbKxA6oKsIQ7zqEA+AJK+7j8eB3ZtoKfuCdvsmWlhCSxRwPzdKu3MZXo9bhj9eSUH0qj+g+FE+hayL/03z91hDnqqFujTtNrqVWwu5+qiS0V5uri8jsn8agTqKMzf09Wwyl1fuj1yzgfS0V0s/4DJyqhcBYMpI8th/i1KCMO5oUOBJQ2LqAhfZb0dM4OtpDzXXJlXoctfPl1zWyp6Ri0RG4pdD9eqBt3fVxflQ4oIkqvrFtiwIxYx5I1EqVWo8c0QSQVkkwMjQNs3D39s2WMTc1FaE6VUYTKBglwVpLWMGD0O9vKy66SUPNEbpaZttDJIzQIJ1w8SwNDIPYPCYKAsyWcYIGG5+mqwMPBamvePJcbVb4O6TnL9gG6sc0A7PWDtenR0LJF3ZgyTDqaZn4YzYSs0w0ggqHL9E4m7laya3mvftXhELuOvWhXX0+TivBpJwFb53rfvUo2S9tZYVs8X/udIPPZGed7hYAJL5n/k5U2h5qdU6CBU+rBAMZvhaG4tHURShhTojQdJfow5aPzfcCeKw5sbHrdC1p9WZxAj1TmK4JLswBX3tdeqUS/10seEPPSy1bbraFRE0EPKgxFeWd1/VYVHeOsMpd+Ra6QaWgcbBC7ao09NjIldaZs5JHDF5N71PDE8NbyT+05gvLU0nEh4LGU6UKN/piRPTnujzl8prroC8S6hgwl3VvKk+cjtvg+fBNEDC4ZlCAQm57LERBrdp8po/Tck8Ao2fi2jBYCpyjQW+ufSzOSiANZlS4vVJIvYJGwuLR5upaLYQTAhLOHeHvXuauYhq5AIdQbW3H0eFj+W34jrfsFbvtC7ImIt8kwHYz66F05jXpy8PprfcUyAUG2aprFdM9pDmytB5J7kw29Q3nNNj7btSICrpxReSpAXTBV4DoQo1yevZjpI0I3YIRWLUgXXKf7k2hG9/S6zrZn0aExD0ha0RdejBPm15kl0pn1Kpx8Ru+XZHxEuzn8JNGpqpCVR/X+lRRmwtbI4wA89gLlRB1JXhKrybwgERY6f/7yfaYYp4Ja0Cgwkt68GMeDZzGECOtW0b4dQRoz8d4nr2d4TnLhfkZGJ+uay6+gnb291r1A25dFL0nYyvIXVaxz0GgEWJFIIr7NwU3LPvf1bk922UmzL2PT3Hei1q7X9n2scTDAagfc0nb+8LrrFHN4OeDX1FBzUcLObbSwtL/jOc1Z9mSu7ADKOEt4TqIUTZL42IgNfIIMecN4UzWK/Q2KYYhj3vxxFIrQ9RbhJ9MS7FnuksZHbXHLqsPve785+7i3vCrr9Av2/mMU+l97zFI8nZyS5PsqaHvNLqyia/Lajt3zmuQXm9FN2lzTDL48/e2hJEOcDvu6i+ApBsG4nEM09xj9rAkXKbp1Wi9UkbdNYUBNcTDRoegoTGvly0erhMQcRHM6so+9h8bCP5wLvE2jbQxnJBRfOfszsFVs7qxj7dsD9/pz9YVk17NWzLapcmCWw7l0VrTwl4Ko1eBftOrYJ3OUizghkHR65tpXo7Yh/EFyyRmXRXPzzRVBbpZBLngkLhaNXRudp/QD+XFpVuQgG5lJTDLKyaNP0ZyQjJMwlYOVWhD7ffsjwKFwQv2U1TDSntdZohD/14xM!; ROLL=7QTn5TwthIayCNcTMp4Qx1VqIifJqoMapLjSpr4x0Lgh8QUVwN0zRTcNa9ypgStEft+axknn5XsYMIVuwoNjA/yaja6rBmF4CQoEhC28sSl3I9axXXyK2NCA7FOFIQOlRREcRxk6mP9ALn675W5PKpxQ9KR7Tf8C4dlWo9t7qs527NWDccOwN8rZt9DGEBsB6hzyuzJllRB9evLpxCkiQ1dTJPitazRA50EYxOSJZtd4zxH7d1d3OT1Vcx+qC9+/CaB3MQu+K/nuTwpHOFQ3H5Ul9peIlbO!']
 -> cookie2 ['$Version=1']
 -> get [['/site=0000127709/mnum=0000162763/genr=1/logs=0/mdtm=1077726643/bins=1', 'HTTP/1.1']]
 -> host ['opera1-servedby.advertising.com']
 -> te ['deflate, gzip, chunked, identity, trailers']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /site=0000127709/mnum=0000162763/genr=1/logs=0/mdtm=1077726643/bins=1
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive, TE']
 -> cookie ['opera2=_419e70fb,,126885^76592&127709^162763_; ACID=ee440010568883680002!; BASE=3QYHXfsNvCFBeLNZ206GJi0j25HWC503TNR4QZW9L+6yd7SDOZsCODkwrUPvF7pLinQW+Y4YpDi5YPXp3N5+/p/sZu9hgUI7z0a7h8r6Oes1R+mMCN4bjFM5MOO4k2/yUHOI5yef5lOUKTgk4VgtzkBHQSQB9kDqCJJ3jQQb21A6fXOCivfNF6vM83kqmm08kM50QUUnDKahIBmM3Rx45ku9NsghF9aN+g4WxQ2UoD4ZWFSEoZ88zDPAUFQ34A8th8LM8F4bW12uOTE5tYLN9ysGCh/7G8eYmPpBUWOk/tvufZu2GZJl8pDoPrCeguTNZv4GwOAYfeSRHikoCHwrfPvDTktVlmC++l9KY1h7fsPeqxRkv/TK+SC45kIyTrbpMKK0lzdzDLPuyv4PHchjRakf3SEOVTgdY9/8u4rI+EgtXApntWoNuyd9u5yZOme/6Z4pXChCsOidcbFNh5NXYnNX2T/M/EXweXfAQwtI56pnfpG0FkYNdXl6iazAOVyDWvVVDavmj4+Hz1uzu/Vwa1AJOuSP6NSCC7nL/ZxT1Cer57QI7GdDQFsr1cjq90nBiuj5xuErfnHOUDBGsOyzQRPOKYNVDD/1KvpbV6du0vmj41LOspU2y5lic8Npu0EPkHMaqhUgFPUp/ZK9Ld/vGET9OG9FER4H9OWCNrVICxbRz3vTbCODW5QBNHueRp5DprIXurB8fzkd8BzTuYAD0Z/wsSw91jgCuK7sWPIvd81AhO3ifMkNB/O7trr+hNMD/5oYZiWTvD+BfFNIjQzgrOI9U0myc73vNKsEr/fez90SyOdmmBBMSc3wvMFEWSMxxuid0b3AM0r6Xjj/CltEdD9UNkPQmxexV2WZvEeLC0Ix6rhiDHUJRmcBc+tHuiJ63VxwZf+D8R+4HlZROv3A1+Egq9BMGDwtocv2tzSj9XAbNk/Vln9bIipJaEroXWp0bJPuSXTNpx3QdF1kq8b0ZCvRupMfbxLu6+e/ngeiJRheKguJxXar6GP5VCsVez0wvavAAsc93qOZkHs9XFxCOilJ2D5+SXs4oGJplC8V8eWZ+rAk7P7w2KF5DD6WNCNCk8Hg0J46RrKWR+koRcoPpFJaVkm2ltuxOUG5wjXONu45RvAjpHczTF5ZPAs/eU9GaZQmrwFbfUIau5711n9HzNHNh5WfqMjGHCxC0Q6+Lkh7MLRGCmMIdO2MO5hn/Y5/oWqgIbRQWDDqPUofY3sVsjR6VqHlcZ7XDPqqN9u71tutiCh6oKRajfWHSLfGosSWvDX/omzxRN0XZ3f8qRzpvlfLF/x/TmvwBYVf2Rtb+x2u4KUwRzsgg4RrBpadQnfg43R7eBO3azlHX64+tdcEqFJaMcl3MgrJBErqQpNfUuiq4mS6AfriEFk/YFr/fz3cPOSqvOmFsQPwkKZJ/O0zlh5sUxNp2/zRfOIY1pkBtYUh3rMgnoP4cUtHb1vLdtDXx9tdL2pX+kKX15K5V7cYF1YRgVI9J/YFxfQcry9yBJue7s9hJaxISsfPjOr1Sflt/o0EpIzOx89S0ho68RVj6VPtHWMtm2kZiU8aUPx0nzTBgXJ5WrXMp+2qaPr+lv0AJSFbmjubXe4IhK55AttSQUvW6FGD6k1CNyMcTKxrYP62lvD!; ROLL=2Mtm4L9DYEwtNoJM2s62b+p57DnLepvaY0VHJi2+rK0RsSruyat2pS8uzWvKR/bQrwJY0sG+V4DkkQHkQEknH6bgwafsOECCySdLJJ9GNx0a2OI/kl1nBjhsbJLtvK53475BduhhhRSQMsglMGCyd/04Ru3d2+voKdloOJGUYbXkBrujzgY+xXEWeG2ErmRdK00ZSsNbtKlb6no3fMIhXaZZoIy8vsOE22X9n9ktD+f/XCDIPjjsUS8kmrXWHTN8PlPnn4lBQoK+CVFle6uPx3Pr2UK2GSL!']
 -> cookie2 ['$Version=1']
 -> get [['/site=0000127709/mnum=0000162763/genr=1/logs=0/mdtm=1077726643/bins=1', 'HTTP/1.1']]
 -> host ['opera2-servedby.advertising.com']
 -> te ['deflate, gzip, chunked, identity, trailers']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /site=0000127709/mnum=0000162763/genr=1/logs=0/mdtm=1077726643/bins=1
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive, TE']
 -> cookie ['opera4=_419e70fc,,126885^76592&127709^162766_; ACID=ee440010568883680002!; BASE=EW1XvbJwCMhkztjPmjKG+pQ3/bXppXenUXuVsKuQHxX4n5IH+IBFPwSJZG36Av7k4ixoB9HR9D7AJ4w6b2xaG7AOfFzpK0Y6qsRoUesyxpnRXdCTYjGi0cEXbj+bb9tCYJgVu4KT8Tj+Ob36XjduF5e1fTNmU9rfNr8eCrYzhOx3k0EjpcYj+04nmwEqC4N/0dB6DsFWMZbcIPcFvxYZAoqn4Lg3dJTi6np4nsThwDyDaWWB9zTAHHDRyWemXEjswLmLbXZuq7S1y6wfci2/Wi0hlJsAsot62I+ggzJWZn7CQaw/XwNMBc1Ic/PfR2K6EIQHYdJQhYpR/n+NfDQWqva2Q59/sPKsSnerHy19Fdv7kyk61eQkJuPua770yEHgbdi6q7gbTgxWIu5EusthYlyEh650jMYSHKnbZd1df1OD2sbNQ9voud+tboCPl0gvetPVo+wWkRgZ6MI0TvT1Zx0+84y5+Npt58Wz08sE5ppJ0XerkvxjlXubjpvzJMhCpkv0RsaIUTL+iIR4iz26F2BU2dEyrxO10uQPj3Z8ojbE/wu0JYMdDIxbIm8vuHKNv2jo1Q5WiM/nR8rk6EMhpySmNyRXJe7U5R0auBM1P5gHwEE1uU5z31j4ElMhBZeubee4g2hY3MqGoyB3rLewXi6FkpE3l8uOu8ZG9Sg1hM+kYE9qoMpPWGTUqNR32My2selJ1nKqqmqdBZU3Ldu7CZ31WX+Sc9h9jbHkqFrugmnL/0aVR5GzrIUsl7byES8j2ssJVB0uud3Aqov0lSbnmtAXgTUqTb3gkUqKlAbNeMQz5uzrsaPmL+NYIw3bMQpIPPK8bsJrvQkRGWqJPAgqR8vJXEShrQ4WVDTei91XTqDp3yAkrh/I7oyuvI7XazszemxwUsnkeueFkt3ha7RIZNacOPBLiy7rrpRZnP4Ar8iHS0kcZ/+GgG1Y2qcTakd9MYXIjYaYZzvbK0EuCIrVBDnTjtW4YzuJ8qZI0QN5AMQ52++1jvFcOW8ui2nBhNaTKJ5zwDOHtEjw84qLjPL7ZhjGDP4RkModeNpB970Oq/T4Aq/Ic1CX0v4QIRefqJ4P1/k3e1+4wpaPtRfKlsYiXlgJktmNberbBphtYiNw0zERtH6tXixS60/ib8VHoSzwlFSYpsydx+Y60R9G23UbjcsMHp6yB5yhuZIEepZo51obKdtCpbD+SQ72GVZTlHDOpiZDILM8Ar378bAVmQm2i1IpBUhWerDHJ/rMCua8rwKE2Tlh6srTH5LHUUG5J45uCpAlMbY1o6Qcy4meLvbZiDKHsS9jwBd2O2SnCcj6dliGG/IZZSDhMfNa2rLHJj7Fzhn7TP50NItB9MpYaWL4jgL5qDaLCqyp50k1GfpSC83rE6x+p17CDWYPOAIcVqr4mPKfhon2D9kd8mUYQKQYreM9OVEYtYdSc8/3wxxGk1NPIDVwWQ6lJR6Qi9Kn7vR+Q62pvzXvzxmz44CM6cbNfxs9GU0f+OYkWoRmTOPyvNDcgUiJRiXHXdP+RWmlcMBcaR+NbX0zJfQWYXD00q59lsVjJxbJfG9TxkIqfke4LcxMD8EMml1yX7VPeCcn9S2O43DM1IMCBndn4Zy7yJXcjnFJQuAKc7ueondn/t+uphLsuGI!; ROLL=hfmEvrLrNLWZ9roJpS97rB9/cbCMC/dp0Z81LwhPEe+EadQAjCusoMpqiKyodr7OSqWq5MdUCL4axcU2IecIJn9HmXniihH8uDJ+lzTOLIdjnxveBaNAyUpihsWiIsZDToBvog9hXvOfbf2m2TYWNifFAiS5u73hU3/7OsPm58SoYNBl7/D+u+ECQKeC9x51C5FEnyisQuKS3emD0ru7gjRC6IQATCwKiVmoqQT3tdLIkhiiNiIEHKZkqMBA1BlG/bJrPO4Fkuiv3PjU8/zd/b2VIwI304E!']
 -> cookie2 ['$Version=1']
 -> get [['/site=0000127709/mnum=0000162766/genr=1/logs=0/mdtm=1077726645/bins=1', 'HTTP/1.1']]
 -> host ['opera4-servedby.advertising.com']
 -> te ['deflate, gzip, chunked, identity, trailers']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /site=0000127709/mnum=0000162766/genr=1/logs=0/mdtm=1077726645/bins=1
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive, TE']
 -> get [['/Websidan/dagbok/dagbok.html', 'HTTP/1.1']]
 -> host ['10.1.1.1']
 -> referer ['http://10.1.1.1/Websidan/index.html']
 -> te ['deflate, gzip, chunked, identity, trailers']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /Websidan/dagbok/dagbok.html
---
dissector.http.headers :
 -> accept-ranges ['bytes']
 -> connection ['close']
 -> content-length [416]
 -> content-type ['text/html; charset=ISO-8859-1']
 -> date ['Sat, 20 Nov 2004 10:21:09 GMT']
 -> etag ['"46a8e-1a0-91374700"']
 -> http/1.1 [['200', 'OK']]
 -> last-modified ['Sun, 14 Mar 2004 22:05:48 GMT']
 -> server ['Apache/2.0.40 (Red Hat Linux)']
dissector.http.is_request False
dissector.http.is_response True
dissector.http.response 00677ea8c324fea3ec47357306deed26
dissector.http.response_protocol 1.1
dissector.http.response_status ['200', 'OK']
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive, TE']
 -> cookie ['opera3=_419e70fc,,126885^76592&127709^162763_; ACID=ee440010568883680002!; BASE=XgfauP+OyydIlr/9I6mjniAgObR+9rYYoRlmZpjmRzkAYblQWoOjXtWNOBAvOZ1ruXHePzkOIoZWjYBVpfD6nFqz9KO7PymOdBTouleNTdS+z5Yo4ofCrwQxRbUEI0EcEBLS2pDxpLP4t+NuVpJAraoUZ3nobZ5lyPLJHBKcPJxBPkiEN/ABNnV0NFgrjhdLGdjuJEZMqNqdx7NlVBR3yIefVWxODFNyDXdBbr6yE0e4nAlk8gUi5Psmjne3te0YPqADGlLD7aw3OBHLttEtR6MRzf5ElU1hmDU2eJ/KTGHu48bgSjNEyBDRtiCGJ6KIG8go3gXW3v7Mz+pz84LD80QaG527QMfbOh58Uf+qt0zhTKrmhpuOTGL3GTXIclQshTFOztkLxJQeE0Dfy4tnp7Ma1Zrm4o2iB0PJOTF+XKRwXT/eywSuKtL2y9PPY3iBevLphMDc/X1rbn44ucFZqTzctzUQbqGEyq9q3VK6KC6NEyh2cbf22JL8a00adQ34KFcI3vBBKDakP24ien5ttBldHXaV7Ch089HkzX4rWPV2dfUSqmB6lrmh7x+SYCvg76JMTj9xhneOkTfgnra+Hmz4mLLeuRMCb6lqvUMIslG0XIUvbknixvyo+dPpWYHkPNxbyhhi5wm8FQPC/qt8PR9ZkpsjvRWR7pTiDhcYGf0qjCrWMGgnEn8uFtHgYEx9gahyFx0y1anVqv0KREvp+CH+D3NxbOH5Y4eani7oLzwFAFJHdEERdRdchjQKIUYCtBSf8pgH325P31vAjy/TYriQpF6RYe3Cy++irjjryfEAtqHozeyzKyzvS9tEKOO8ScH7PJqHgJTwjA0t/sgawjDrSTeUN4mrYQTd8Vk4BiSrzDmVEL56jcO2aIwFsdsUnQqyCNrk35+Lp/G/dhVvTor2ZJ8R5bXgcpi9oX4YPWUjNYRtEb1cy41MF6KOMogyBXZB2+hP1RVJbJkKeEqQ1mzjnC6ZzMWHZjrMCB2L1uHWtNqYPkFh6BuBEH3j8fbskjHzSi1JMKH3QZunktSC/2M+gOEL0iSvXo6a3I0AxA+B6UumM/ogVc7B0esHMLbN2Klgpr3uqwvTprXoUqJJVd+Bo84NksN6Sv8KkR58g96yRRb4BLRDsILlEIDSCxb30Dz/xMabFd08YGSkAo5v5PhCXzdb/DqlwJsQcX6xLedJ/myhRYo9ALIwO6bJzHJ9Ep3B2fT3UR6+1DxVcB+BAXYkfzF/+J8nM74yKY3zzp9xydIDDghah+NWJb2/sHLkr7K2J3xT0wHNJAUbrCrPeRzy2WUR7S+E/MH/50rQUo0pFjNX4qWxCqi5sOUWw1zjZCn940anLczwr8KGwgl4vw7x6TE6xv/hUCag/4HsNwK+QS+u/MKpciTmDEPBhMNuI35zrh73Ehy+9kAWRActBomf5bJ2VNzlZT9DeLIFYjEO3COYO265sZXzuauBeGuRii2kRmee2iMc7fyuLy/swPJb6kVOEEEET4R1bVfdmWQHMZhl22ErsnDd6kBolhQddXXXZoUeCB3/geBeKEeGKXmKibWcwewyjX9B8PiK/5EnHsAw1oYVioAMLdoXDAQO8gQmh7qofMuvBieAyx7a/6u5AF0JB64hkI3OSyQL64G71bD!; ROLL=2SflxnACP87TN5KYCWCJd5KAbjFR8F5iksg98EMHA3mxU1pKASxLy1sFfb9YIKFmjn+R07cyySmvhyeXEkU1UQ9ChGKdtqDJ3JSm/vlSsibTWLVdmZnz7ubajzop9ybjN1irbCzIlRgH896qZteR+PTt4l4fH118UXee5KrZ21j7xRQpiLcW7c6xi3rVIDhpAtepPlSi76aEZGjTNc0nfz2+mEF238ov2fCEAyZR3WA7fYPx6yKntE/+xoWhl5Olf4iSbRynLTqeD58bgRvTYQfeIFjMgJH!']
 -> cookie2 ['$Version=1']
 -> get [['/site=0000127709/mnum=0000162763/genr=1/logs=0/mdtm=1077726643/bins=1', 'HTTP/1.1']]
 -> host ['opera3-servedby.advertising.com']
 -> te ['deflate, gzip, chunked, identity, trailers']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /site=0000127709/mnum=0000162763/genr=1/logs=0/mdtm=1077726643/bins=1
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive, TE']
 -> get [['/Websidan/dagbok/2004/dagbok.html', 'HTTP/1.1']]
 -> host ['10.1.1.1']
 -> referer ['http://10.1.1.1/Websidan/dagbok/dagbok.html']
 -> te ['deflate, gzip, chunked, identity, trailers']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /Websidan/dagbok/2004/dagbok.html
---
dissector.http.headers :
 -> accept-ranges ['bytes']
 -> connection ['close']
 -> content-length [1263]
 -> content-type ['text/html; charset=ISO-8859-1']
 -> date ['Sat, 20 Nov 2004 10:21:11 GMT']
 -> etag ['"1fab4-4ef-a2927cc0"']
 -> http/1.1 [['200', 'OK']]
 -> last-modified ['Wed, 14 Jul 2004 19:31:39 GMT']
 -> server ['Apache/2.0.40 (Red Hat Linux)']
dissector.http.is_request False
dissector.http.is_response True
dissector.http.response 289e7e38a40c7d01fef5f1179eb567e7
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive, TE']
 -> get [['/Websidan/dagbok/2004/28/dagbok.html', 'HTTP/1.1']]
 -> host ['10.1.1.1']
 -> referer ['http://10.1.1.1/Websidan/dagbok/2004/dagbok.html']
 -> te ['deflate, gzip, chunked, identity, trailers']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /Websidan/dagbok/2004/28/dagbok.html
---
dissector.http.headers :
 -> accept-ranges ['bytes']
 -> connection ['close']
 -> content-length [2232]
 -> content-type ['text/html; charset=ISO-8859-1']
 -> date ['Sat, 20 Nov 2004 10:21:12 GMT']
 -> etag ['"75912-8b8-9e9d8d80"']
 -> http/1.1 [['200', 'OK']]
 -> last-modified ['Sun, 18 Jul 2004 18:57:10 GMT']
 -> server ['Apache/2.0.40 (Red Hat Linux)']
dissector.http.is_request False
dissector.http.is_response True
dissector.http.response f3104b8171aacd09763668f402b594bc
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive, TE']
 -> get [['/Websidan/2004-07-SeaWorld/320/DSC07858.JPG', 'HTTP/1.1']]
 -> host ['10.1.1.1']
 -> referer ['http://10.1.1.1/Websidan/dagbok/2004/28/dagbok.html']
 -> te ['deflate, gzip, chunked, identity, trailers']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /Websidan/2004-07-SeaWorld/320/DSC07858.JPG
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive, TE']
 -> get [['/Websidan/2004-07-SeaWorld/320/DSC07859.JPG', 'HTTP/1.1']]
 -> host ['10.1.1.1']
 -> referer ['http://10.1.1.1/Websidan/dagbok/2004/28/dagbok.html']
 -> te ['deflate, gzip, chunked, identity, trailers']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /Websidan/2004-07-SeaWorld/320/DSC07859.JPG
---
dissector.http.headers :
 -> accept-ranges ['bytes']
 -> connection ['close']
 -> content-length [8963]
 -> content-type ['image/jpeg']
 -> date ['Sat, 20 Nov 2004 10:21:13 GMT']
 -> etag ['"2b7fd-2303-299b0d80"']
 -> http/1.1 [['200', 'OK']]
 -> last-modified ['Sun, 18 Jul 2004 14:49:42 GMT']
 -> server ['Apache/2.0.40 (Red Hat Linux)']
 -> x-pad ['avoid browser bug']
dissector.http.is_request False
dissector.http.is_response True
dissector.http.response 835d8e7a12d31c4bbe4eeff7b4b5ab3b
---
dissector.http.headers :
 -> accept-ranges ['bytes']
 -> connection ['close']
 -> content-length [10730]
 -> content-type ['image/jpeg']
 -> date ['Sat, 20 Nov 2004 10:21:13 GMT']
 -> etag ['"2b7fe-29ea-29c8d440"']
 -> http/1.1 [['200', 'OK']]
 -> last-modified ['Sun, 18 Jul 2004 14:49:45 GMT']
 -> server ['Apache/2.0.40 (Red Hat Linux)']
dissector.http.is_request False
dissector.http.is_response True
dissector.http.response 0951a03339a81693ed8987c43b6dd1ba
---
dissector.http.browser Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]
dissector.http.headers :
 -> accept ['application/x-shockwave-flash,text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,video/x-mng,image/png,image/jpeg,image/gif;q=0.2,text/css,*/*;q=0.1']
 -> accept-charset ['windows-1252, utf-8, utf-16, iso-8859-1;q=0.6, *;q=0.1']
 -> accept-encoding ['deflate, gzip, x-gzip, identity, *;q=0']
 -> accept-language ['en']
 -> connection ['Keep-Alive, TE']
 -> get [['/Websidan/2004-07-SeaWorld/fullsize/DSC07858.JPG', 'HTTP/1.1']]
 -> host ['10.1.1.1']
 -> referer ['http://10.1.1.1/Websidan/dagbok/2004/28/dagbok.html']
 -> te ['deflate, gzip, chunked, identity, trailers']
 -> user-agent ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) Opera 7.11  [en]']
dissector.http.is_request True
dissector.http.is_response False
dissector.http.language en
dissector.http.request_protocol HTTP/1.1
dissector.http.request_uri GET /Websidan/2004-07-SeaWorld/fullsize/DSC07858.JPG
---
dissector.http.headers :
 -> accept-ranges ['bytes']
 -> connection ['close']
 -> content-length [191515]
 -> content-type ['image/jpeg']
 -> date ['Sat, 20 Nov 2004 10:21:17 GMT']
 -> etag ['"7593f-2ec1b-a77d1dc0"']
 -> http/1.1 [['200', 'OK']]
 -> last-modified ['Sun, 18 Jul 2004 14:13:19 GMT']
 -> server ['Apache/2.0.40 (Red Hat Linux)']
dissector.http.is_request False
dissector.http.is_response True
dissector.http.response 74da406ca3055d0e56080b796c670ee3
---
"""

import hashlib

from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager

class Tester(Plugin, PassiveAudit):
    def parse_http(self, mpkt):
        if not mpkt.cfields:
            return

        keys = filter(lambda x: x.startswith('dissector.http'),
                      mpkt.cfields.keys())
        keys.sort()

        for key in keys:
            value = mpkt.cfields[key]

            if key == 'dissector.http.request' or \
               key == 'dissector.http.response':

                value = hashlib.md5(value).hexdigest()

            if isinstance(value, dict):
                print key, ":"

                dk = value.keys()
                dk.sort()

                for k in dk:
                    print " ->", k, value[k]
            else:
                print key, value

        print "---"

    def register_decoders(self):
        AuditManager().add_to_hook_point('http', self.parse_http)

    def stop(self):
        AuditManager().remove_from_hook_point('http', self.parse_http)

__plugins__ = [Tester]
