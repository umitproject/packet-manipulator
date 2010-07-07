#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009 Adriano Monteiro Marques
#
# Author: Quek Shu Yang <quekshuy@gmail.com>
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

from tagger import get_summary

ROLE_STRING_MASTER  = 'M'
ROLE_STRING_SLAVE   = 'S'

try:
    from umit.pm.core.logger import log
except ImportError: 
    from sniffcommon import log
    
try: 
    from umit.pm.backend.scapy import MetaPacket
except ImportError:
    log.debug('Packet.py: not in PM Context')
    class BtMetaPacket(object):
        
        def __init__(self, unit):
            self.pkt = unit 

        def __getattr__(self, name):
            return getattr(self.pkt, name)
else:
    
    ###
    ### Only if we are in the context of PM 
    ### do we formally define BtMetaPacket
    ###
    
    class BtMetaPacket(MetaPacket):
        """
            SniffPacket wrapper. Contains application level information as well. 
        """
        
        NOT_IMPLEMENTED = ['hashret', 'answers', 'insert', 
                           'complete', 'remove', 'get_datetime',
                           'get_time', 'get_source', 'get_dest',
                           'reset', 'get_protocol_bounds', 'haslayer',
                           'getlayer', 'get_raw_layer',
                           'rebuild_from_raw_payload', 'get_datalink',
                           'copy' ]
        
        def __init__(self, sniffunit, cfields = None):
            super(BtMetaPacket, self).__init__(cfields)
            self.sniffunit = sniffunit
    #    def __init__(self, proto=None, cfields=None):
    #        self.root = proto
    #        self.cfields = cfields or {}
    
        def __div__(self, other):
            """
                Implemented to maintain consistency with original implementation
                of MetaPacket. Only manipulate custom fields
            """
            cfields = self.cfields.copy()
            cfields.update(other.cfields)
            self.cfields = cfields
            
            return self
            
        def __getattr__(self, name):
            if name in self.NOT_IMPLEMENTED:
                log.debug('BTMetaPacket call to %s' % name)
                raise NotImplementedError('Not required as yet with BTMetaPackets')
        
        @classmethod
        def new(cls, proto_name):
            """ Keep. For future use when attacking is possible"""
            raise NotImplementedError('Incompatible with BTMetaPackets')
        
        def get_channel(self):
            return str(self.sniffunit.chan)
        
        def get_clock(self):
            return str(self.sniffunit.clock)
        
        def get_role(self):
            return ROLE_STRING_MASTER if self.sniffunit.is_src_master else ROLE_STRING_SLAVE
    
        def get_raw(self):
            return self.sniffunit.payload.rawdata
        
        def summary(self):
            # TODO: Implement packet tagging
            return get_summary(self.sniffunit.payload)
    
        def get_protocol_str(self):
            return ''
    
        def get_protocols(self):
            "@returns a list containing the name of protocols"
            log.debug('BTMetaPacket: call to get_protocols')
            return []
        
        # Custom fields
    
        def get_cfield(self, name):
            return self.cfields[name]
    
        def set_cfield(self, name, val):
            self.cfields[name] = val
    
        def unset_cfield(self, name):
            del self.cfields[name]