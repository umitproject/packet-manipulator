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
HTTP protocol dissector (Passive audit).

This module uses TCP reassembler exposed in TCP decoder.
>>> from umit.pm.core.auditutils import audit_unittest
>>> audit_unittest('-f ethernet,ip,tcp,http', 'http-digest.pcap')
dissector.http.info HTTP DIGEST : 10.0.2.102:1093 <-> 10.0.1.101:80 USERNAME: Susan PASSWORD: realm=INS.COM, qop=auth, algorithm=MD5-sess, uri=/Security/Digest/, nonce=20d1da125f2fc6013eec4a6f4d1cf34133fffe449de04ce7f6b8e6110c0ee23867e01f774a96c8d5, nc=00000001, cnonce=52447499ed25edfa526e88d3623882ed, response=6e33ca77c2acbbc5ffc38df51b2f5702
"""

from base64 import b64decode
from struct import pack, unpack
from socket import inet_ntoa

from urllib import unquote

from umit.pm.core.atoms import defaultdict
from umit.pm.core.logger import log
from umit.pm.core.errors import PMErrorException
from umit.pm.gui.plugins.core import Core
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager
from umit.pm.core.const import PM_TYPE_STR, PM_TYPE_DICT, PM_TYPE_BOOLEAN

HTTP_NAME = 'dissector.http'
HTTP_PORTS = (80, 8080)
HTTP_TRAILER = '\r\n\r\n'

NTLM_WAIT_RESPONSE = 0

FORM_USERNAME = 0
FORM_PASSWORD = 1

HTTP_REQUEST  = 0
HTTP_RESPONSE = 1

g_fields = None

def form_extract(data, type=FORM_USERNAME):
    global g_fields

    if not g_fields:
        return None

    for pattern in unquote(data).split('&'):
        try:
            k, v = pattern.split('=', 1)
            if g_fields[k] == type:
                return v
        except:
            pass

class HTTPRequest(object):
    def __init__(self, sess, manager):
        self.headers_complete = False
        self.content_length = -1
        self.chunked = False
        self.headers = defaultdict(list)
        self.body = ''
        self.chunks = [(-1, '')]

        self.session = sess
        self.manager = manager
        self.http_type = HTTP_REQUEST

    def feed(self, mpkt, data):
        """
        @return a tuple (bool, int) with bool = True if the response/request
                parsing is complete. The int is the last data count.
        """
        if not self.headers_complete:
            end_ptr = self._parse_headers(mpkt, data)

            if self.headers_complete:
                # If the body is missing continue processing

                finished = self._check_finished()

                if not finished:
                    remaining = data[end_ptr:]

                    if not remaining:
                        return False, end_ptr # Not finished. Body missing

                    ret = self._parse_body(remaining, end_ptr)

                    if ret[0] == True:
                        self.analyze_headers(mpkt)
                        self._parse_post(mpkt)

                        if self.http_type == HTTP_REQUEST:
                            mpkt.set_cfield(HTTP_NAME + '.request',
                                            self.body)
                        else:
                            mpkt.set_cfield(HTTP_NAME + '.response',
                                            self.body)

                        self.manager.run_hook_point('http', mpkt)

                        # We have finished processing our response/request
                        # at this stage.

                    return ret

                self.analyze_headers(mpkt)
                self.manager.run_hook_point('http', mpkt)

                return finished, end_ptr

            return False, end_ptr
        else:
            ret = self._parse_body(data)

            if ret[0]:
                self.analyze_headers(mpkt)
                self._parse_post(mpkt)

                if self.http_type == HTTP_REQUEST:
                    mpkt.set_cfield(HTTP_NAME + '.request', self.body)
                else:
                    mpkt.set_cfield(HTTP_NAME + '.response', self.body)

                self.manager.run_hook_point('http', mpkt)

            return ret

    def _check_finished(self):
        if self.content_length > 0:
            return self.content_length == len(self.body)

        if self.chunked:
            return False

        if 'post' in self.headers:
            return False

        return True

    def _parse_headers(self, mpkt, payload):
        idx = payload.find(HTTP_TRAILER)

        if idx >= 0:
            header_part = payload[:idx]
            self.headers_complete = True
        else:
            last = payload.rfind('\r\n')

            if last == 0:
                return 2
            if last == -1:
                return 0

            header_part = payload[:last]

        for line in header_part.splitlines():
            if not line:
                break

            try:
                key, value = line.split(' ', 1)
            except:
                # FIXME: dirty hack.
                # Handle headers like Host:127.0.0.1
                key, value = line.split(':', 1)
                key += ':'

            if key[-1] == ':':
                key = key[:-1].lower()
            else:
                key = key.lower()
                value = value.rsplit(' ', 1)

                if key.upper() == 'GET':
                    self._parse_get(mpkt, value[0])

            if key == 'content-length':
                try:
                    value = int(value)
                    self.content_length = value
                except ValueError:
                    pass

            elif key == 'transfer-encoding':
                self.chunked = True

            elif key.startswith('http/'):
                mpkt.set_cfield(HTTP_NAME + '.response_protocol', key[5:])
                mpkt.set_cfield(HTTP_NAME + '.response_status', value)

            elif key == 'authorization' or \
                 key == 'www-authenticate':
                if value[0:9].upper() == 'PASSPORT ':
                    self._parse_passport(mpkt, value[9:])
                elif value[0:5].upper() == 'NTLM ' and self.session:
                    self._parse_ntlm(mpkt, value[5:])
                elif value[0:6].upper() == 'BASIC ':
                    self._parse_basic(mpkt, value[6:])
                elif value[0:7].upper() == 'DIGEST ':
                    self._parse_digest(mpkt, value[7:])
                elif value[0:5] == 'NTLM ':
                    self._parse_ntlm(mpkt, value[5:])

            self.headers[key].append(value)


        if self.headers_complete:
            return idx + 4
        else:
            return last

    def analyze_headers(self, mpkt):
        if not self.headers:
            return

        mpkt.set_cfield(HTTP_NAME + '.headers', self.headers)

        if self.http_type == HTTP_REQUEST:
            mpkt.set_cfield(HTTP_NAME + '.is_request', True)
            mpkt.set_cfield(HTTP_NAME + '.is_response', False)

            for req in ('get', 'post', 'head'):
                if req in self.headers:
                    mpkt.set_cfield(HTTP_NAME + '.request_uri',
                                    req.upper() + " " + self.headers[req][0][0])
                    mpkt.set_cfield(HTTP_NAME + '.request_protocol',
                                    self.headers[req][0][1])
                    break

            if 'user-agent' in self.headers:
                mpkt.set_cfield(HTTP_NAME + '.browser',
                                self.headers['user-agent'][0])

            if 'accept-language' in self.headers:
                mpkt.set_cfield(HTTP_NAME + '.language',
                                self.headers['accept-language'][0])
        else:
            mpkt.set_cfield(HTTP_NAME + '.is_request', False)
            mpkt.set_cfield(HTTP_NAME + '.is_response', True)

            if 'server' in self.headers:
                mpkt.set_cfield('banner', self.headers['server'][0])

    def _parse_get(self, mpkt, val):
        idx = val.find('?')

        if idx < 0:
            return

        val = val[idx + 1:]

        username = form_extract(val)
        password = form_extract(val, FORM_PASSWORD)

        if username and password:
            mpkt.set_cfield('username', username)
            mpkt.set_cfield('password', password)

            self.report(mpkt, 'GET', username, password)

    def _parse_post(self, mpkt):
        # Export chunked body as list instead as string
        # and avoid parsing that

        if self.chunked:
            self.body = map(lambda x: x[1], self.chunks)
            return

        # No Post header in headers. Don't procede
        if not 'post' in self.headers:
            return

        username = form_extract(self.body)
        password = form_extract(self.body, FORM_PASSWORD)

        if username and password:
            mpkt.set_cfield('username', username)
            mpkt.set_cfield('password', password)

            self.report(mpkt, 'POST', username, password)

    def _parse_passport(self, mpkt, val):
        # TODO: implement me.
        pass

    def _parse_digest(self, mpkt, val):
        values = []
        found = False
        user = ''

        try:
            for value in val.split(','):
                ret = value.strip().split('=', 1)

                if isinstance(ret, list) and len(ret) == 2:
                    k, v = ret

                    if v[0] == v[-1] and (v[0] == '"' or v[0] == '\''):
                        v = v[1:-1]

                    if k.upper() == 'USERNAME':
                        user = v
                        found = True
                    else:
                        values.append(k + "=" + v)
        finally:
            if found:
                password = ', '.join(values)

                mpkt.set_cfield('username', user)
                mpkt.set_cfield('password', password)

                self.report(mpkt, 'DIGEST', user, password)

    def _parse_ntlm(self, mpkt, val):
        val = b64decode(val)
        ident, msgtype = unpack('8sI', val[0:12])

        if msgtype == 2:
            challenge_data = unpack('8B', val[24:32])

            s = ''
            for i in challenge_data:
                s += '%02X' % i

            self.session.data = (NTLM_WAIT_RESPONSE, s)

        elif msgtype == 3:
            if self.session.data and self.session.data[0] == NTLM_WAIT_RESPONSE:
                ulen, umaxlen, uoffset = unpack('HHI', val[36:44])
                lmlen, lmmaxlen, lmoffset = unpack('HHI', val[12:20])
                ntlen, ntmaxlen, ntoffset = unpack('HHI', val[20:28])

                username = ''
                ret = val[uoffset:uoffset + ulen]

                for i in xrange(0, len(ret), 2):
                    username += chr(ord(ret[i]) & 0x7f)

                password = 'NTLM: '
                for i in val[lmoffset:lmoffset + 24]:
                    password += '%02X' % ord(i)

                password += ':'
                for i in val[ntoffset:ntoffset + 24]:
                    password += '%02X' % ord(i)

                password += ':' + self.session.data[1]

                mpkt.set_cfield('username', username)
                mpkt.set_cfield('password', password)

                self.report(mpkt, 'NTLM', username, password)

                self.session.data = None

    def _parse_basic(self, mpkt, val):
        val = b64decode(val)
        ret = val.split(':', 1)

        if isinstance(ret, tuple) and len(ret) == 2:
            mpkt.set_cfield('username', ret[0])
            mpkt.set_cfield('password', ret[1])

            self.report(mpkt, 'BASIC', ret[0], ret[1])

    def _parse_body(self, payload, end_ptr=0):
        if self.chunked:
            idx = 0
            clen, cbody = self.chunks[-1]

            if clen == -1:
                idx = payload.find('\r\n')

                if idx == 0:
                    idx = payload.find('\r\n', 2)

                if idx < 0:
                    return False, end_ptr

                clen = int(payload[:idx], 16)
                idx += 2

                if clen == 0:
                    #self.body = '\r\n'.join(map(lambda x: x[1], self.chunks))
                    return True, idx

            real = payload[idx:]
            missing = clen - len(cbody)

            if missing > 0:
                captured = min(len(real), missing)
                cbody += real[:captured]

                self.chunks[-1] = (clen, cbody)

                if len(cbody) == clen:
                    self.chunks.append((-1, ''))
                    return False, captured + idx + end_ptr
                elif len(cbody) > clen:
                    raise Exception('This is impossible')
                else:
                    return False, captured + idx + end_ptr
            elif missing == 0:
                self.chunks.append((-1, ''))
                return False, idx + end_ptr
            elif missing < 0:
                raise Exception('This should not happen')

        elif self.content_length > 0:
            missing = self.content_length - len(self.body)

            if missing > 0:
                captured = min(len(payload), missing)
                self.body += payload[:captured]

                if len(self.body) == self.content_length:
                    return True, captured + end_ptr
                elif len(self.body) > self.content_length:
                    raise Exception('This is impossible')
                else:
                    return False, captured + end_ptr

            elif missing == 0:
                return True, end_ptr
            elif missing < 0:
                raise Exception('This should not happen')

        else:
            self.body += payload
            return True, len(payload) + end_ptr

    def report(self, mpkt, typ, username, password):
        if self.http_type == HTTP_RESPONSE:
            src = (mpkt.l3_src, mpkt.l4_src)
            dst = (mpkt.l3_dst, mpkt.l4_dst)
        else:
            src = (mpkt.l3_dst, mpkt.l4_dst)
            dst = (mpkt.l3_src, mpkt.l4_src)

        self.manager.user_msg(
            'HTTP %s : %s:%d <-> %s:%d USERNAME: %s PASSWORD: %s' % \
            (typ, src[0], src[1], dst[0], dst[1],
             username, password),
            6, HTTP_NAME)

class HTTPResponse(HTTPRequest):
    def __init__(self, sess, manager):
        HTTPRequest.__init__(self, sess, manager)

        self.http_type = HTTP_RESPONSE

class HTTPSession(object):
    def __init__(self, manager):
        self.manager = manager
        self.request = HTTPRequest(self, manager)
        self.response = HTTPResponse(self, manager)

        self.requests = [self.request]
        self.responses = [self.response]

        self.req_last_len = 0
        self.res_last_len = 0

        self.data = None

    def feed_request(self, hlfstream, mpkt):
        while hlfstream.count > self.req_last_len:
            ret, idx = self.request.feed(mpkt,
                                         hlfstream.data[self.req_last_len:])

            if idx == 0:
                return

            self.req_last_len += idx

            if ret == True:
                self.request = HTTPRequest(self, self.manager)
                self.requests.append(self.request)

    def feed_response(self, hlfstream, mpkt):
        while hlfstream.count > self.res_last_len:
            ret, idx = self.response.feed(mpkt,
                                          hlfstream.data[self.res_last_len:])

            if idx == 0:
                return

            self.res_last_len += idx

            if ret == True:
                self.response = HTTPResponse(self, self.manager)
                self.responses.append(self.response)


class HTTPDissector(Plugin, PassiveAudit):
    def start(self, reader):
        self.sessions = {}
        self.manager = AuditManager()

        conf = self.manager.get_configuration(HTTP_NAME)

        self.reassemble = conf['reassemble']

        if self.reassemble:
            tcpdecoder = Core().get_need(reader, 'TCPDecoder')

            if not tcpdecoder:
                raise PMErrorException('TCPDecoder plugin not loaded.')

            if not tcpdecoder.reassembler:
                raise PMErrorException('TCP segments reassembling disabled '
                                       'in TCPDecoder.')

            self.tcpdecoder = tcpdecoder
            tcpdecoder.reassembler.add_analyzer(self._tcp_callback)

        ufields = conf['username_fields']
        pfields = conf['password_fields']

        global g_fields

        g_fields = dict(
            map(lambda x: (x, FORM_USERNAME), ufields.split(',')) +  \
            map(lambda x: (x, FORM_PASSWORD), pfields.split(','))
        )

    def stop(self):
        conf = self.manager.get_configuration(HTTP_NAME)

        if not self.reassemble:
            for port in HTTP_PORTS:
                self.manager.remove_dissector(APP_LAYER_TCP, port,
                                              self._http_decoder)
        else:
            self.tcpdecoder.remove_analyzer(self._tcp_callback)

        self.manager.deregister_hook_point('http')

    def register_decoders(self):
        self.manager.register_hook_point('http')

        if not self.reassemble:
            for port in HTTP_PORTS:
                self.manager.add_dissector(APP_LAYER_TCP, port,
                                           self._http_decoder)

    def _http_decoder(self, mpkt):
        payload = mpkt.data

        if not payload:
            return None

        try:
            obj = HTTPRequest(None, self.manager)
            obj.feed(mpkt, payload)

            found = False

            for type in ('get', 'post', 'head'):
                if type in obj.headers:
                    found = True
                    break

            if not found:
                obj.http_type = HTTP_RESPONSE
                obj.analyze_headers(mpkt)
        except Exception, exc:
            pass

    def _tcp_callback(self, stream, mpkt):
        if stream.dport in HTTP_PORTS or \
           stream.sport in HTTP_PORTS:
            stream.listeners.append(self._process_http)

    def _process_http(self, stream, mpkt, rcv):
        if stream not in self.sessions:
            sess = HTTPSession(self.manager)
            self.sessions[stream] = sess
        else:
            sess = self.sessions[stream]

        sess.feed_response(stream.client, mpkt)
        sess.feed_request(stream.server, mpkt)

        if stream.state in (CONN_RESET, CONN_CLOSE, CONN_TIMED_OUT):
            del self.sessions[stream]

        return REAS_COLLECT_DATA


__plugins__ = [HTTPDissector]
__plugins_deps__ = [('HTTPDissector', ['TCPDecoder'], ['=HTTPDissector-1.0'], [])]

__audit_type__ = 0
__protocols__ = (('tcp', 80), ('tcp', 8080), ('http', None))
__configurations__ = (('global.cfields', {
    HTTP_NAME + '.response' : (PM_TYPE_STR, 'HTTP response body'),
    HTTP_NAME + '.request' : (PM_TYPE_STR, 'HTTP request body'),
    HTTP_NAME + '.is_response' : (PM_TYPE_BOOLEAN,
                                  'True if it\'s and HTTP response'),
    HTTP_NAME + '.is_request' : (PM_TYPE_BOOLEAN,
                                 'True if it\'s an HTTP request'),
    HTTP_NAME + '.headers' : (PM_TYPE_DICT, 'A dict containing the headers'),
    HTTP_NAME + '.browser' : (PM_TYPE_STR, 'A string indicating the UserAgent'),
    HTTP_NAME + '.language' : (PM_TYPE_STR, 'A string indicating the language '
                               'used by the client'),
    HTTP_NAME + '.response_status' : (PM_TYPE_STR, 'The status string used by '
                                      'the server to serve a request'),
    HTTP_NAME + '.request_uri' : (PM_TYPE_STR,
                                  'The URI requested by the client'),
    HTTP_NAME + '.request_protocol' : (PM_TYPE_STR, 'The version of HTTP '
                                       'protocol used by the client'),
    HTTP_NAME + '.response_protocol' : (PM_TYPE_STR, 'The version of HTTP '
                                       'protocol used by the server'),
    }),

    (HTTP_NAME, {
    'reassemble' : [True, 'Reassemble TCP flows. Enable it also in TCP.'],
    'form_extract' : [True, 'Try to extract username/password also from forms'],
    'username_fields' : ["login,user,email,username,userid,form_loginname,"
                         "loginname,pop_login,uid,id,user_id,screenname,uname,"
                         "ulogin,acctname,account,member,mailaddress,"
                         "membername,login_username,login_email,uin,sign-in",

                         'A coma separated string of possible username fields'],

    'password_fields' : ["pass,password,passwd,form_pw,pw,userpassword,pwd,"
                         "upassword,login_password,passwort,passwrd",

                         'A coma separated string of possible password fields'],
    }),
)
__vulnerabilities__ = (('HTTP dissector', {
    'description' : 'Hypertext Transfer Protocol (HTTP) is an '
                    'application-level protocol for distributed, collaborative,'
                    'hypermedia information systems.[1] Its use for retrieving '
                    'inter-linked resources led to the establishment of the '
                    'World Wide Web.\n\n'
                    'HTTP development was coordinated by the World Wide Web '
                    'Consortium and the Internet Engineering Task Force '
                    '(IETF), culminating in the publication of a series of '
                    'Requests for Comments (RFCs), most notably RFC 2616 '
                    '(June 1999), which defines HTTP/1.1, the version of HTTP '
                    'in common use.\n\n'
                    'HTTP is a request/response standard of a client and a '
                    'server. A client is the end-user, the server is the web '
                    'site. The client making a HTTP request using a web '
                    'browser, spider, or other end-user tool is referred to as '
                    'the user agent. The responding server which stores or '
                    'creates resources such as HTML files and images is called '
                    'the origin server. In between the user agent and origin '
                    'server may be several intermediaries, such as proxies, '
                    'gateways, and tunnels. HTTP is not constrained to using '
                    'TCP/IP and its supporting layers, although this is its '
                    'most popular application on the Internet. Indeed HTTP can '
                    'be "implemented on top of any other protocol on the '
                    'Internet, or on other networks." HTTP only presumes a '
                    'reliable transport; any protocol that provides such '
                    'guarantees can be used."',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                            'Hypertext_Transfer_Protocol'), )
    }),
)

