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

from __future__ import with_statement

import os
import md5

from threading import RLock
from tempfile import mkstemp
from xml.dom.minidom import parseString

from PM.Core.I18N import _
from PM.Core.Logger import log
from PM.Core.Const import PM_PLUGINS_TEMP_DIR

from PM.Gui.Plugins.Network import *
from PM.Gui.Plugins.Atoms import Version

STATUS_IDLE = 0

LATEST_ERROR = 1
LATEST_GETTED = 2
LATEST_GETTING = 3

FILE_ERROR = 4
FILE_GETTED = 5
FILE_GETTING = 6
FILE_CHECKING = 7

class UpdateObject(object):
    def __init__(self, obj):
        self.buffer = []
        
        self.status = STATUS_IDLE
        
        self.label = None
        self.fract = None
        
        self.url = None
        self.version = None
        self.hash = None
        
        self.object = obj
        
        self.fd = None
        
        self.size = None
        self.total = None

        # Simple lock for sync
        self.lock = RLock()

    def parse_latest_file(self):
        """
        @return url, version or None, None on error
        """

        try:
            doc = parseString("".join(self.buffer))
            
            if doc.documentElement.tagName != 'UmitPluginUpdate':
                raise Exception("Not valid xml file.")

            url, version, hash = None, None, None

            for node in doc.documentElement.childNodes:
                if node.nodeName == 'update-uri':
                    url = node.firstChild.data
                if node.nodeName == 'version':
                    version = node.firstChild.data
                if node.nodeName == 'md5':
                    hash = node.firstChild.data

            return url, version, hash
        except Exception, exc:
            log.warning("__parse_xml: %s" % exc)
            return None, None, None


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
            filename = os.path.basename(obj.object.reader.get_path())
            
            obj.fd = open(mkstemp(".part", filename, \
                          PM_PLUGINS_TEMP_DIR)[1], "wb+")
                         
            Network.get_url(obj.url, self.__process_plugin, obj)
        except Exception, err:
            obj.status = FILE_ERROR
            obj.label = err
            obj.fract = None
            
            self.__process_next_download()
    
    def __process_plugin(self, file, data, exc, obj):
        """
        Process callback for plugin data
        """

        if isinstance(exc, ErrorNetException):

            with obj.lock:
                obj.status = FILE_ERROR
                obj.label = exc.reason
                obj.fract = 1
                
                self.__process_next_download()
                return
        
        elif isinstance(exc, StopNetException):
            if obj.hash:

                data = ""

                with obj.lock:
                    obj.label = _('Checking validity ...')
                    obj.status = FILE_CHECKING
                
                    obj.fd.flush()
                    obj.fd.seek(0)

                    data = obj.fd.read()
                
                # Not locked it could freeze the ui
                hasher = md5.new()
                hasher.update(data)
                
                with obj.lock:
                    if hasher.hexdigest() == obj.hash:
                        obj.label = _('Updated. Restart to take effect')
                        obj.status = FILE_GETTED
                    else:
                        obj.label = _('Corrupted file.')
                        obj.status = FILE_ERROR
            else:
                with obj.lock:
                    obj.label = _('Updated. Restart to take effect')
                    obj.status = FILE_GETTED
            
            with obj.lock:
                obj.fd.close()
                obj.fract = 1
            
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
            with obj.lock:
                try:
                    obj.status = FILE_GETTING
                    obj.size = 0
                    obj.total = int(file.info()['Content-Length'])
                except:
                    pass
            
                obj.label = _('Downloading ...')

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
        Network.get_url("%s/latest.xml" % obj.object.reader.update, \
                        self.__process_manifest, obj)

    def __process_manifest(self, file, data, exc, obj):
        """
        Callback to parse latest.xml file containing meta information about
        the avaiable update.
        """

        if isinstance(exc, ErrorNetException):
            with obj.lock:
                obj.status = LATEST_ERROR
                obj.label = _('Cannot find newer version (%s)') % exc.reason
                
                self.__process_next()
                return
        
        elif isinstance(exc, StopNetException):
            url, version, hash = obj.parse_latest_file()

            new_v = Version(version)
            cur_v = Version(obj.object.reader.version)

            type = -1 # -1 no action / 0 update / 1 downgrade

            if new_v > cur_v:
                type = 0
            elif cur_v < new_v:
                type = 1

            with obj.lock:
                if url and version and type >= 0:

                    # We check if the path is the plugins in config_dir

                    plug_dir = os.path.join(Path.config_dir, 'plugins')

                    if os.path.dirname(obj.object.reader.get_path()) != plug_dir and \
                       os.access(plug_dir, os.O_RDWR):

                        obj.status = LATEST_ERROR

                        if not type:
                            obj.label = _('Version %s avaiable but need manual update.') % version
                        else:
                            obj.label = _('Version %s avaiable but need manual downgrade.') % version
                    else:
                        obj.status = LATEST_GETTED
                        obj.label = _('Version %s avaiable.') % version
                    
                    obj.version = version
                    obj.url = url
                    obj.hash = hash
                else:
                    obj.status = LATEST_ERROR

                    if type < 0:
                        obj.label = _('Unable to parse latest.xml')
                    else:
                        obj.label = _('No applicable updates found')

                self.__process_next()

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
