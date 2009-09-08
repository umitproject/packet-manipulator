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

from static import StaticContext

from umit.pm.core.logger import log
from umit.pm.backend.abstract.context import register_timed_context

class BaseTimedContext(StaticContext):
    """
    A TimedContext could be stopped/paused/resumed/restarted
    and should be asynchronous so use threads to avoid UI freeze.

    Use has_stop/has_pause/has_restart attribute to choose
    what actions is supported by your TimedContext
    """

    NOT_RUNNING, RUNNING, PAUSED = range(3)

    # Select the suport operations
    has_stop = True
    has_pause = True
    has_restart = True

    def __init__(self):
        self._state = self.NOT_RUNNING
        self._percentage = 0.0
        self._last = 0

        StaticContext.__init__(self, '')

    def _start(self):
        "The real start method you should override this"
        self.state = self.RUNNING
        return True

    def _resume(self):
        "The real resume method you should override this"
        self.state = self.RUNNING
        return True

    def _restart(self):
        "The real restart method you should override this"
        self.state = self.RUNNING
        return True

    def _stop(self):
        "The real stop method you should override this"
        self.state = self.NOT_RUNNING
        return True

    def _pause(self):
        "The real pause method you should override this"
        self.state = self.PAUSED
        return True

    def join(self):
        "Join the child thread"
        pass

    def is_alive(self):
        "Ponderate about overriding"
        return self._state != self.NOT_RUNNING

    def start(self):
        log.debug('Starting %s TimedContext ...' % self)
        if self.state != self.RUNNING:
            if self._start():
                log.debug('%s TimedContext correctly started.' % self)
                return True
        log.debug('Failed to start %s TimedContext.' % self)
        return False

    def pause(self):
        log.debug('Pausing %s TimedContext ...' % self)
        if self.state == self.RUNNING:
            if self._pause():
                log.debug('%s TimedContext correctly paused.' % self)
                return True
        log.debug('Failed to pause %s TimedContext.' % self)
        return False

    def stop(self):
        log.debug('Stopping %s TimedContext ...' % self)
        if self.state == self.RUNNING:
            if self._stop():
                log.debug('%s TimedContext correctly stopped.' % self)
                return True
        log.debug('Failed to stop %s TimedContext.' % self)
        return False

    def restart(self):
        log.debug('Restarting %s TimedContext ...' % self)
        if self.state != self.RUNNING:
            if self._restart():
                log.debug('%s TimedContext correctly restarted.' % self)
                return True
        log.debug('Failed to restart %s TimedContext.' % self)
        return False

    def resume(self):
        log.debug('Resuming %s TimedContext ...' % self)
        if self.state != self.RUNNING:
            if self._resume():
                log.debug('%s TimedContext correctly resumed.' % self)
                return True
        log.debug('Failed to resume %s TimedContext.' % self)
        return False

    def get_state(self):
        return self._state
    def set_state(self, val):
        self._state = val

    def get_percentage(self):
        if self.state == self.NOT_RUNNING:
            self._percentage = 100.0
        return self._percentage
    def set_percentage(self, val):
        self._percentage = val

    # Returns the last data
    def get_data(self):
        end = len(self.data)
        lst = self.data[self._last:]
        self._last = end
        return lst

    def get_all_data(self):
        return self._data

    state = property(get_state, set_state, \
            doc="The TimedContext state (NOT_RUNNING/RUNNING/PAUSED)")

    percentage = property(get_percentage, set_percentage, \
            doc="The percentage of the timed context or None\n" \
                "If None you should set the percentage to a random? value\n" \
                "see pulse attribute in gtk.CellRendererProgress")

TimedContext = register_timed_context(BaseTimedContext)
