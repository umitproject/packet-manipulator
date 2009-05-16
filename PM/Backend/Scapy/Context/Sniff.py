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

import fcntl
import tempfile

from datetime import datetime
from subprocess import Popen
from threading import Thread, Lock

import gobject

from PM.Core.I18N import _
from PM.Core.Logger import log
from PM.Core.Atoms import with_decorator
from PM.Manager.PreferenceManager import Prefs

from PM.Backend.Scapy import *

def register_sniff_context(BaseSniffContext):
    class SniffContext(BaseSniffContext):
        """
        A sniff context for controlling various options.
        """
        has_stop = True
        has_pause = False
        has_restart = True

        def __init__(self, *args, **kwargs):
            BaseSniffContext.__init__(self, *args, **kwargs)

            self.lock = Lock()
            self.prevtime = None
            self.socket = None
            self.internal = True
            self.process = None

            self.title = _('%s capture') % self.iface
            self.summary = _('Sniffing on %s') % self.iface
            self.thread = None
            self.priv = []

        @with_decorator
        def get_all_data(self):
            return BaseSniffContext.get_all_data(self)

        @with_decorator
        def get_data(self):
            return BaseSniffContext.get_data(self)

        @with_decorator
        def set_data(self, val):
            self.data = val

        def get_percentage(self):
            if self.state != self.RUNNING:
                return 100.0
            else:
                if self.stop_count or \
                   self.stop_time or \
                   self.stop_size or \
                   self.capmethod == 1:
                    return self.percentage
                else:
                    return None

        def _start(self):
            self.prevtime = datetime.now()

            if self.iface:
                try:
                    self.socket = conf.L2listen(type=ETH_P_ALL,
                                                iface=self.iface,
                                                filter=self.filter)
                except socket.error, (errno, err):
                    self.summary = str(err)
                    return False
                except Exception, err:
                    self.summary = str(err)
                    return False

            self.state = self.RUNNING
            self.internal = True
            self.data = []

            if self.capmethod == 0:
                self.thread = Thread(target=self.run)

            elif self.capmethod == 1 or \
                 self.capmethod == 2 or \
                 self.capmethod == 3:

                 self.thread = Thread(target=self.run_helper)

            self.thread.setDaemon(True)
            self.thread.start()

            return True

        def _stop(self):
            if self.internal:
                self.internal = False

                if self.socket:
                    self.socket.close()

                # We have to kill the process directly from here because the
                # select function is blocking to avoid CPU burning.

                if self.process:
                    log.debug('Asynchronous process termination requested.')
                    log.debug('Killing process %s with pid: %d' % \
                              (self.process, self.process.pid))

                    self.process.kill()
                    self.process = None

                return True
            else:
                return False

        def _restart(self):
            if self.thread and self.thread.isAlive():
                return False

            # Ok reset the counters and begin a new sniff session
            self.tot_size = 0
            self.tot_time = 0
            self.tot_count = 0

            return self._start()

        def run_helper(self):
            """
            This function is the thread main procedure for the thread that spawn
            a new process like tcpdump to avoid packet loss and reads MetaPacket
            from the pcap file managed from a private process.
            """

            helper = process = errstr = None

            if self.capmethod == 2:
                helper = Prefs()['backend.tcpdump'].value

                if self.stop_count:
                    helper += "-c %d " % self.stop_count

                helper += " -vU -i%s -w%s"

                log.debug("I'm using tcpdump helper to capture packets")

            elif self.capmethod == 3:
                helper = Prefs()['backend.dumpcap'].value

                if self.stop_count:
                    helper += "-c %d " % self.stop_count

                if self.stop_time:
                    helper += "-a duration:%d " % self.stop_time

                if self.stop_size:
                    helper += "-a filesize:%d " % self.stop_size / 1024

                helper += " -i%s -w%s"

                log.debug("I'm using dumpcap helper to capture packets")

            else:
                log.debug("I'm using virtual interface method")

            if helper:
                # TODO: Probably will be better to have a class that organizes
                #       all the temporary files and than remove them all after
                #       the program will closed.

                outfile = tempfile.mktemp('.pcap', 'PM-')

                self.process = subprocess.Popen(helper % (self.iface, outfile),
                                                shell=True, close_fds=True,
                                                stderr=subprocess.PIPE)

                if os.name != 'nt':
                    log.debug("Setting O_NONBLOCK stderr file descriptor")

                    flags = fcntl.fcntl(self.process.stderr, fcntl.F_GETFL)

                    if not self.process.stderr.closed:
                        fcntl.fcntl(self.process.stderr, fcntl.F_SETFL,
                                    flags| os.O_NONBLOCK)

                # TODO: Fix code for nt system. Probably we should use
                #       PeekNamedPipe function.

                log.debug("Process spawned as `%s` with pid %d" % \
                          ((helper % (self.iface, outfile), self.process.pid)))
                log.debug("Helper started on interface %s. Dumping to %s" % \
                          (self.iface, outfile))
            else:
                outfile = self.cap_file

            try:
                # Dummy method probably is better to read the stdout in async
                # way and get the number of packets and continue if n > 0

                while self.internal and self.capmethod != 1 and \
                      (not os.path.exists(outfile) or \
                       os.stat(outfile).st_size != 20):

                    log.debug("Dumpfile not ready. Waiting 0.5 sec")
                    time.sleep(0.5)

                log.debug("Dumpfile seems to be ready.")

                if self.internal:
                    if self.capmethod == 1:
                        outfile_size = float(os.stat(outfile).st_size)
                    else:
                        outfile_size = None

                    log.debug("Creating a PcapReader object instance")

                    reader = PcapReader(outfile)

                    if getattr(reader.f, 'fileobj', None):
                        # If fileobj is present we are gzip file and we
                        # need to get the absolute position not the
                        # relative to the gzip file.
                        position = reader.f.fileobj
                    else:
                        position = reader.f

            except OSError, err:
                errstr = err.strerror
                self.internal = False
            except Exception, err:
                errstr = str(err)
                self.internal = False

            reported_packets = 0

            log.debug("Entering in the main loop")

            while self.internal:
                inp, out, err = select([process.stderr],
                                       [process.stderr],
                                       [process.stderr])

                if process.stderr in inp:
                    line = process.stderr.read()

                    if not line:
                        continue

                # Here dumpcap use '\rPackets: %u ' while tcpdump 'Got %u\r'
                # over stderr file. We use simple split(' ')[1]

                try:
                    report_idx = int(line.split(' ')[1])

                    if report_idx == reported_packets:
                        continue
                    elif report_idx < reported_packets:
                        log.debug('Some kind of error happened here.')
                except Exception, err:
                    continue

                for x in xrange(report_idx - reported_packets):

                    pkt = reader.read_packet()

                    if not pkt:
                        continue

                    pkt = MetaPacket(pkt)
                    packet_size = pkt.get_size()

                    if not pkt:
                        continue

                    if self.max_packet_size and \
                       packet_size - self.max_packet_size > 0:

                        log.debug("Skipping current packet (max_packet_size)")
                        continue

                    if self.min_packet_size and \
                       packet_size - self.min_packet_size < 0:

                        log.debug("Skipping current packet (min_packet_size)")
                        continue

                    self.tot_count += 1
                    self.tot_size += packet_size

                    now = datetime.now()
                    delta = now - self.prevtime
                    self.prevtime = now

                    if delta == abs(delta):
                        self.tot_time += delta.seconds

                    self.data.append(pkt)

                    # callback here

                    lst = []

                    if self.stop_count:
                        lst.append(float(float(self.tot_count) /
                                         float(self.stop_count)))
                    if self.stop_time:
                        lst.append(float(float(self.tot_time) /
                                         float(self.stop_time)))
                    if self.stop_size:
                        lst.append(float(float(self.tot_size) /
                                         float(self.stop_size)))

                    if outfile_size:
                        lst.append(position / outfile_size)

                    if lst:
                        self.percentage = float(float(sum(lst)) /
                                                float(len(lst))) * 100.0

                        if self.percentage >= 100:
                            self.internal = False
                    else:
                        # ((goject.G_MAXINT / 4) % gobject.G_MAXINT)
                        self.percentage = (self.percentage + 536870911) % \
                                          gobject.G_MAXINT

                reported_packets = report_idx

            log.debug("Exiting from thread")

            if self.process:
                log.debug('Killing helper %s with pid: %d' % (self.process,
                                                              self.process.pid))
                self.process.kill()

            self.exit_from_thread(errstr)

        def run(self):
            errstr = None

            while self.internal and self.socket is not None:
                r = None
                inmask = [self.socket]

                try:
                    if WINDOWS:
                        try:
                            r = self.socket.recv(MTU)
                        except PcapTimeoutElapsed:
                            continue
                    else:
                        inp, out, err = select(inmask, inmask, inmask, None)
                        if self.socket in inp:
                            r = self.socket.recv(MTU)
                    if r is None:
                        continue

                    self.priv.append(r)
                except Exception, err:
                    errstr = str(err)
                    self.internal = False
                    self.socket = None
                    break

            self.exit_from_thread(errstr)

        def exit_from_thread(self, errstr=None):
            log.debug("Exiting from thread")

            self.priv = []

            self.state = self.NOT_RUNNING
            self.percentage = 100.0
            status = ""

            if self.tot_size >= 1024 ** 3:
                status = "%.1f GB/" % (self.tot_size / (1024.0 ** 3))
            elif self.tot_size >= 1024 ** 2:
                status = "%.1f MB/" % (self.tot_size / (1024.0 ** 2))
            else:
                status = "%.1f KB/" % (self.tot_size / (1024.0))

            if self.tot_time >= 60 ** 2:
                status += "%d h/" % (self.tot_time / (60 ** 2))
            elif self.tot_time >= 60:
                status += "%d m/" % (self.tot_time / 60)
            else:
                status += "%d s/" % (self.tot_time)

            status += "%d pks" % (self.tot_count)

            if errstr:
                self.summary = _('Error: %s (%s)') % (errstr, status)
            else:
                self.summary = _('Finished sniffing on %s (%s)') % (self.iface,
                                                                    status)

            if self.callback:
                self.callback(None, self.udata)

        def check_finished(self):
            if self.capmethod != 0:
                return

            priv = self.priv
            self.priv = []

            for r in priv:
                # This code should not be in the thread and called in the
                # main thread of the GUI so we can avoid packet loss.
                # It's better to have a temporary list object to store raw
                # packets captured from socket.recv(MTU) function and then joins
                # everything in self.data

                packet = MetaPacket(r)
                packet_size = packet.get_size()

                if self.max_packet_size and \
                   packet_size - self.max_packet_size > 0:

                    log.debug("Skipping current packet (max_packet_size)")
                    continue

                if self.min_packet_size and \
                   packet_size - self.min_packet_size < 0:

                    log.debug("Skipping current packet (min_packet_size)")
                    continue

                self.tot_count += 1
                self.tot_size += packet.get_size()

                now = datetime.now()
                delta = now - self.prevtime
                self.prevtime = now

                if delta == abs(delta):
                    self.tot_time += delta.seconds

                self.data.append(packet)

                # FIXME: This probably should be moved inside the run() function
                if self.callback:
                    self.callback(MetaPacket(packet), self.udata)

                lst = []

                if self.stop_count:
                    lst.append(float(float(self.tot_count) /
                                     float(self.stop_count)))
                if self.stop_time:
                    lst.append(float(float(self.tot_time) /
                                     float(self.stop_time)))
                if self.stop_size:
                    lst.append(float(float(self.tot_size) /
                                     float(self.stop_size)))

                if lst:
                    self.percentage = float(float(sum(lst)) /
                                            float(len(lst))) * 100.0

                    if self.percentage >= 100:
                        self.internal = False
                else:
                    # ((goject.G_MAXINT / 4) % gobject.G_MAXINT)
                    self.percentage = (self.percentage + 536870911) % 2147483647

    return SniffContext
