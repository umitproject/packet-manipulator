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

from umit.pm.core.logger import log
from sniffsession import SniffSession
from sequencesession import SequenceSession
from auditsession import AuditSession

class SessionType:
    types = {}
    sessions = []
    _refcount = 0

    @staticmethod
    def add_session(session):
        session.session_id = SessionType._refcount
        SessionType._refcount += 1

        setattr(SessionType, "%s_SESSION" % session.session_name,
                session.session_id)

        SessionType.types[session.session_id] = session
        SessionType.types[session] = session.session_id

        SessionType.sessions.append(session)

        log.debug("Registering %s (%d, %s)" % (session,
                                               session.session_id,
                                               session.session_name))

        return session.session_id

    @staticmethod
    def remove_session(session):
        del SessionType.types[session.session_id]
        del SessionType.types[session]

        log.debug("Deregistering %s (%d, %s)" % (session,
                                                 session.session_id,
                                                 session.session_name))

SessionType.add_session(SequenceSession)
SessionType.add_session(SniffSession)
SessionType.add_session(AuditSession)
