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

from umit.pm.backend.scapy.packet import *
from umit.pm.backend.scapy.wrapper import *
from umit.pm.backend.scapy.utils import *
from umit.pm.backend.scapy.doc import apply_doc

apply_doc()

PMField             = Field
PMFlagsField        = FlagsField

PMBitField          = None
PMIPField           = IPField

# Check out for presence of IPv6 support
PMIP6Field          = getattr(scapy, "IP6Field", None)
PMMACField          = MACField
PMByteField         = ByteField
PMShortField        = ShortField
PMLEShortField      = LEShortField
PMIntField          = IntField
PMSignedIntField    = SignedIntField
PMLEIntField        = LEIntField
PMLESignedIntField  = LESignedIntField
PMLongField         = LongField
PMLELongField       = LELongField
PMStrField          = StrField
PMLenField          = LenField
PMRDLenField        = RDLenField
PMFieldLenField     = FieldLenField
PMBCDFloatField     = BCDFloatField
PMBitField          = BitField
PMEnumField         = EnumField
