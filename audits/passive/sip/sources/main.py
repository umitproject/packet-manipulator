#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008 Adriano Monteiro Marques
#
# Author: Francesco Piccinno <stack.box@gmail.com>
# Author: Guilherme Rezende <guilhermebr@gmail.com>
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
SIP protocol dissector (Passive audit)
"""

from umit.pm.core.logger import log
from umit.pm.gui.plugins.engine import Plugin
from umit.pm.manager.auditmanager import *
from umit.pm.manager.sessionmanager import SessionManager

SIP_NAME = 'dissector.sip'
SIP_PORTS = (5060, 5061)

SIP_REQUEST  = 0
SIP_RESPONSE = 1

sip_fields = None

class SipSession(object):
     
     def __init__(self, mpkt, manager, sessions, sip_type):
          self.manager = manager
          self.payload = mpkt.data
           
          self.sess = sessions.lookup_session(mpkt, SIP_PORTS, SIP_NAME)
          
          if not self.sess:
               self.sess = sessions.lookup_session(mpkt, SIP_PORTS, SIP_NAME, True)
               self.sess.data = dict(
                    map(lambda x: (x, 'None'), sip_fields.split(','))
               )
                         
          #remove first line from payload    
          end = self.payload.find('\r\n')
          self.payload = self.payload[end +2:]
          
          end = self.payload.find('\r\n')

          while end is not -1:
               tmp = self.payload[:end].split(': ')
               if tmp[0] in self.sess.data:
                    if self.sess.data[tmp[0]] is 'None':
                         self.sess.data[tmp[0]] = tmp[1]
                         print '%s => %s' % (tmp[0], tmp[1])


               self.payload = self.payload[end + 2:]
               end = self.payload.find('\r\n')
               
          
          if sip_type == SIP_REQUEST:
               return self.sip_request(mpkt)
          else: 
               return self.sip_response(mpkt)
          
         

            
     def sip_request(self, mpkt):
          req_type = ''  
          if self.payload.startswith('REGISTER'):
               req_type = 'REGISTER'
                              
          elif self.payload.startswith('INVITE'):
               req_type = 'INVITE'
               
              
          """
          #test.....
          for k, v in self.sess.data.iteritems():
               if v is 'None':
                    start = self.payload.find(k)
                    print start
                    a = self.payload[start:]
                    print a
                    end = a.find('\n')
                    print end
                    print self.payload[start:end]
          """

               
          self.manager.user_msg('SIP REQUEST %s: %s:%d' % \
                           (req_type, mpkt.l3_src, mpkt.l4_src), 6, SIP_NAME)

     def sip_response(self, mpkt):
       
          self.manager.user_msg('SIP RESPONSE: %s:%d'  % \
                           (mpkt.l3_src, mpkt.l4_src),
                           6, SIP_NAME)
   
    
class SIPMonitor(Plugin, PassiveAudit):
     def start(self, reader):
          self.manager = AuditManager()
          self.sessions = SessionManager()
       
          conf = self.manager.get_configuration(SIP_NAME)
          
          global sip_fields
                         
          sip_fields = conf['sip_fields']
          

     def register_decoders(self):

          self.manager.register_hook_point('sip')

          for port in SIP_PORTS:
               self.manager.add_dissector(APP_LAYER_UDP, port,
                                          self.__sip_dissector)
        

     def stop(self):
          for port in SIP_PORTS:
               self.manager.remove_dissector(APP_LAYER_UDP, port,
                                             self.__sip_dissector)
               
               self.manager.deregister_hook_point('sip')
               
     def __sip_dissector(self, mpkt):
          
          payload = mpkt.data

          
          if not payload:
               return None
          
          #print payload

          pos = payload.find('SIP/')
          
          if pos == 0:
               sip_type = SIP_RESPONSE
          elif pos != -1:
               sip_type = SIP_REQUEST
          else:
               return None
          
          obj = SipSession(mpkt, self.manager, self.sessions, sip_type)

                 
__plugins__ = [SIPMonitor]
__plugins_deps__ = [('SIPDissector', ['UDPDecoder'], ['SIPDissector-1.0'], []),]
__author__ = ['Guilherme Rezende']
__audit_type__ = 0
__protocols__ = (('udp', 5060), ('udp', 5061), ('sip', None))
__configurations__ = ((SIP_NAME, {
    'sip_fields' : ["Contact,To,Via,From,User-Agent,Server,Authorization,WWW-Authenticate",

                    'A coma separated string of sip fields'],
    }),
)
__vulnerabilities__ = (('SIP dissector', {
    'description' : 'SIP Monitor plugin'
        'The Session Initiation Protocol (SIP) is an IETF-defined signaling protocol,'
        'widely used for controlling multimedia communication sessions'
        'such as voice and video calls over' 
        'Internet Protocol (IP). The protocol can be used for creating,'
        'modifying and terminating two-party (unicast) or multiparty (multicast)'
        'sessions consisting of one or several media streams.'
        'The modification can involve changing addresses or ports, inviting more' 
        'participants, and adding or deleting media streams. Other feasible'
        'application examples include video conferencing, streaming multimedia distribution,'
        'instant messaging, presence information, file transfer and online games.'
        'SIP was originally designed by Henning Schulzrinne and Mark Handley starting in 1996.'
        'The latest version of the specification is RFC 3261 from the IETF Network Working'
        'Group. In November 2000, SIP was accepted as a 3GPP signaling protocol and permanent'
        'element of the IP Multimedia Subsystem (IMS) architecture for IP-based streaming'
        'multimedia services in cellular systems.',
    'references' : ((None, 'http://en.wikipedia.org/wiki/'
                            'Session_Initiation_Protocol'), )
    }),
)