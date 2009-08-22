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

import os

try:
    from hashlib import md5
    from hashlib import sha1 as sha
except ImportError:
    from md5 import md5
    from sha import sha

from threading import RLock
from tempfile import mkstemp
from StringIO import StringIO
from xml.dom.minidom import parseString

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.const import PM_PLUGINS_TEMP_DIR, PM_PLUGINS_DIR, PM_HOME

from umit.pm.gui.plugins.network import *
from umit.pm.gui.plugins.atoms import Version

STATUS_IDLE = 0

LATEST_ERROR = 1
LATEST_GETTED = 2
LATEST_GETTING = 3

FILE_ERROR = 4
FILE_GETTED = 5
FILE_GETTING = 6
FILE_CHECKING = 7

from xml.sax import handler, make_parser

class Update(object):
    def __init__(self, version, description, url, integrity):
        self.version, self.description, self.url, self.integrity = \
            version, description, url, integrity

class UpdateObject(handler.ContentHandler):
    def __init__(self, obj):
        self.data = ''
        self.parse_phase = 0
        self.updates = []

        self.version = ''
        self.description = ''
        self.url = []
        self.integrity = {}

        self.buffer = []

        self.status = STATUS_IDLE

        self.label = None
        self.fract = None

        self.object = obj

        self.fd = None

        self.size = None
        self.total = None

        self.last_update_idx = 0
        self.selected_update_idx = -1

        # Simple lock for sync
        self.lock = RLock()

    def parse_latest_file(self):
        parser = make_parser()
        parser.setContentHandler(self)
        parser.parse(StringIO("".join(self.buffer)))

    def startElement(self, name, attrs):
        if name == 'UmitPluginUpdate' and self.parse_phase == 0:
            self.parse_phase = 1
        elif name == 'update' and self.parse_phase == 1:
            self.parse_phase = 2
        elif name in ('version', 'description', 'url') and \
             self.parse_phase == 2:

            self.parse_phase = 3
        elif name == 'integrity' and self.parse_phase == 2 and \
             'type' in attrs.keys() and 'value' in attrs.keys():

            self.integrity[attrs.get('type')] =  attrs.get('value')
        else:
            self.data = ''

    def characters(self, ch):
        if self.parse_phase == 3:
            self.data += ch

    def endElement(self, name):
        if name in ('version', 'description', 'url'):
            val = getattr(self, name, None)

            if isinstance(val, basestring):
                setattr(self, name, self.data)
            elif isinstance(val, list):
                val.append(self.data)

        elif name == 'update':
            if self.version and self.url:
                self.updates.append(Update(self.version, self.description,
                                     self.url, self.integrity))

            self.version = ''
            self.description = ''
            self.url = []
            self.integrity = {}
            self.parse_phase = 1
            self.data = ''
        else:
            self.parse_phase -= 1
            self.data = ''

class UpdateEngine(object):
    """
    A class that permits the updating stuff
    """

    def __init__(self):
        "Initialize an UpdateEngine"
        self.update_lst = None
        self.static_lst = None
        self.updating = False

    def stop(self):
        "Mark as stopped"
        self.updating = False

    def start_update(self):
        """
        Start the update phase (getting the latest.xml files).
        You have to set the list first.
        Do nothing if already started.

        Remember to call stop on finish.
        """

        if not self.updating:

            for obj in self.update_lst:
                obj.status = LATEST_GETTING

            self.__process_next()

        self.updating = True

    def start_download(self):
        """
        Start the download phas (getting the real files)
        You have to set the list first.
        Do nothing if already started.

        Remember to call stop on finish.
        """

        if not self.updating:

            for obj in self.update_lst:
                obj.status = FILE_GETTING

            self.__process_next_download()

        self.updating = True

    def __process_next_download(self):
        """
        Process the next avaiable download in the list
        """

        if not self.update_lst:
            return

        obj = self.update_lst.pop(0)

        try:
            user_dir = PM_HOME
            filename = os.path.basename(obj.object.reader.get_path())

            obj.fd = open(mkstemp(".part", filename, \
                          PM_PLUGINS_TEMP_DIR)[1], "wb+")

            Network.get_url(
                # Maybe too long string? :P
                obj.updates[obj.selected_update_idx].url[obj.last_update_idx],
                self.__process_plugin, obj
            )
        except Exception, err:
            obj.status = FILE_ERROR
            obj.label = err
            obj.fract = None

            self.__process_next_download()

    def __remove_file(self, obj):
        try:
            obj.fd.close()
            os.remove(obj.fd.name)
        except:
            log.error('Error while removing temp %s file' % obj.fd.name)

    def __process_plugin(self, file, data, exc, obj):
        """
        Process callback for plugin data
        """

        if isinstance(exc, ErrorNetException):
            obj.lock.acquire()

            try:
                if obj.last_update_idx + 1 < \
                   len(obj.updates[obj.selected_update_idx].url):

                    obj.last_update_idx += 1

                    obj.status = FILE_GETTING
                    obj.label = _('Cycling to next update url. Waiting...')
                else:
                    obj.status = FILE_ERROR
                    obj.label = _('Download failed: %s') % str(exc.reason)
                    obj.fract = 1

                self.__remove_file(obj)

                self.__process_next_download()
                return
            finally:
                obj.lock.release()

        elif isinstance(exc, StopNetException):
            #TODO: CHECK THIS
            if obj.updates[obj.selected_update_idx].integrity:

                data = ""
                obj.lock.acquire()

                try:
                    obj.label = _('Checking validity ...')
                    obj.status = FILE_CHECKING

                    obj.fd.flush()
                    obj.fd.seek(0)

                    data = obj.fd.read()
                finally:
                    obj.lock.release()

                # Not locked it could freeze the ui
                md5_hash = sha_hash = None
                sums = obj.updates[obj.selected_update_idx].integrity

                if 'md5' in sums:
                    md5_hash = md5(data)
                if 'sha1' in sums:
                    sha_hash = sha(data)

                obj.lock.acquire()

                try:
                    if (md5_hash and md5_hash.hexdigest() == sums['md5']) or \
                       (sha_hash and sha_hash.hexdigest() == sums['sha1']):

                        obj.label = _('Updated. Restart to take effect')
                        obj.status = FILE_GETTED
                    else:
                        obj.label = _('Corrupted file.')
                        obj.status = FILE_ERROR
                finally:
                    obj.lock.release()

            else:
                obj.lock.acquire()

                try:
                    obj.label = _('Updated. Restart to take effect')
                    obj.status = FILE_GETTED
                finally:
                    obj.lock.release()

            obj.lock.acquire()

            try:
                obj.fd.close()
                obj.fract = 1
            finally:
                obj.lock.release()

            try:
                if obj.status == FILE_ERROR:
                    os.remove(obj.fd.name)
                else:
                    os.rename(obj.fd.name, \
                              obj.fd.name[:obj.fd.name.index(".ump") + 4])
            except Exception:
                # TODO: add more sensed control?
                pass

            self.__process_next()

        elif isinstance(exc, StartNetException):
            obj.lock.acquire()

            try:
                try:
                    obj.status = FILE_GETTING
                    obj.size = 0
                    obj.total = int(file.info()['Content-Length'])
                except:
                    pass

                obj.label = _('Downloading ...')
            finally:
                obj.lock.release()

        elif not exc:
            if obj.total:
                obj.size += len(data)
                obj.fract = float(obj.size) / float(obj.total)
            obj.fd.write(data)

    def __process_next(self):
        """
        Forward to the next update (download the next latest.xml)
        """

        if not self.update_lst:
            return

        obj = self.update_lst.pop(0)
        obj.label = _('Downloading update information...')

        Network.get_url("%s/latest.xml" % \
                        obj.object.reader.update[obj.last_update_idx], \
                        self.__process_manifest, obj)

    def __process_manifest(self, file, data, exc, obj):
        """
        Callback to parse latest.xml file containing meta information about
        the avaiable update.
        """

        if isinstance(exc, ErrorNetException):
            obj.lock.acquire()

            try:
                if obj.last_update_idx + 1 < len(obj.object.reader.update):
                    obj.last_update_idx += 1

                    obj.status = LATEST_GETTING
                    obj.label = _('Cycling to next update url. Waiting...')

                    self.update_lst.append(obj)
                elif isinstance(exc, ErrorNetException):
                    obj.status = LATEST_ERROR
                    obj.label = _('Cannot find newer version (%s)') % exc.reason

                self.__process_next()
                return
            finally:
                obj.lock.release()

        elif isinstance(exc, StopNetException):
            try:
                obj.parse_latest_file()
            except Exception, exc:

                if obj.last_update_idx + 1 < len(obj.object.reader.update):
                    obj.last_update_idx += 1

                    obj.status = LATEST_GETTING
                    obj.label = _('Cycling to next update url. Waiting...')

                    self.update_lst.append(obj)
                else:
                    obj.status = LATEST_ERROR
                    obj.label = _('Cannot find newer version (%s)') % str(exc)

                self.__process_next()
                return

            version = None
            type = -1 # -1 no action / 0 update / 1 downgrade

            # If we have only 1 update..
            if len(obj.updates) == 1:
                version = obj.updates[0].version

                new_v = Version(version)
                cur_v = Version(obj.object.reader.version)

                if new_v > cur_v:
                    type = 0
                elif cur_v < new_v:
                    type = 1

            obj.lock.acquire()

            try:
                if obj.updates:

                    # We check if the path is the plugins in config_dir


                    if os.path.dirname(obj.object.reader.get_path()) != PM_PLUGINS_DIR and \
                       os.access(PM_PLUGINS_DIR, os.O_RDWR):

                        obj.status = LATEST_ERROR

                        if type == -1:
                            obj.label = _('Various versions available but require manual intervention.')
                        elif type == 0:
                            obj.label = _('Version %s available but need manual update.') % version
                        elif type == 1:
                            obj.label = _('Version %s available but need manual downgrade.') % version
                    else:
                        obj.status = LATEST_GETTED
                        if type == -1:
                            obj.label = _('Various versions available')
                        else:
                            obj.label = _('Version %s available.') % version

                else:
                    obj.status = LATEST_ERROR

                    if type < 0:
                        obj.label = _('Unable to parse latest.xml')
                    else:
                        obj.label = _('No applicable updates found')

                self.__process_next()
            finally:
                obj.lock.release()

        elif not exc:
            obj.buffer.append(data)

    def get_list(self):
        "Getter for list"
        return self.static_lst

    def set_list(self, value):
        "Setter for list"
        lst = []

        for iter in value:
            if isinstance(iter, UpdateObject):
                lst.append(iter)
            else:
                lst.append(UpdateObject(iter))

        self.update_lst = lst
        self.static_lst = tuple(self.update_lst)

    list = property(get_list, set_list)

if __name__ == "__main__":
    parser = make_parser()
    loader = UpdateObject(1)
    parser.setContentHandler(loader)
    parser.parse(open('test.xml'))
    print loader.updates
