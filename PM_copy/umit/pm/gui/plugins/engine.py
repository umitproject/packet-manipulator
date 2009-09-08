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

import os
import sys
import os.path

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.atoms import Singleton
from umit.pm.core.const import PM_DEVELOPMENT, \
                          PM_PLUGINS_DIR, \
                          PM_PLUGINS_TEMP_DIR, \
                          PM_PLUGINS_DOWNLOAD_DIR

from umit.pm.gui.plugins.core import Core
from umit.pm.gui.plugins.tree import PluginsTree, PluginException
from umit.pm.gui.plugins.containers import PluginReader, BadPlugin

from umit.pm.manager.auditmanager import AuditManager

from umit.pm.manager.preferencemanager import Prefs

class Plugin(object):
    """
    Plugin base class
    """
    def start(self, reader):
        "This is the main for your plugin (reader could be None if testing)"
        pass

    def stop(self):
        "This is the exit point of you plugin"
        pass

class PluginPath(object):
    """
    a PluginPath object mantains a dict of Plugins contained in a dir

    >>> p = PluginPath("/blah")
    >>> p.get_plugins()
    {}
    """

    def __init__(self, path):
        """
        The default constructor

        @param path the path to search in for plugin
        """
        self.path = path
        self.scanned = False
        self._plugins = {} # a dict should be great ;)

    def scan_path(self):
        """
        Walk the path passed in the constructor for .ump files,
        then save the found plugins on a dict that could be accesed with
        get_plugins()

        No recursive scan, only top-level directory is considerated.
        """

        if self.scanned or not os.path.exists(self.path):
            return

        for file in os.listdir(self.path):
            path = os.path.join(self.path, file)

            if file.endswith(".ump") and \
               os.path.isfile(path):

                try:
                    reader = PluginReader(path)

                    for conf_name, conf_dict in reader.configurations:
                        AuditManager().register_configuration(conf_name,
                                                               conf_dict)
                except BadPlugin, exp:
                    log.info("%s" % exp)
                    continue

                self._plugins[file] = reader

        self.scanned = True

    def reset(self):
        "Reset the PluginPath object"

        self.scanned = False
        self._plugins = {}

    def get_plugins(self):
        """
        Start the scan_path if it's not already started and then return a dict
        containing the usable plugins.

        @return a dict like
            key   => file.ump
            value => PluginReader()
        """
        self.scan_path()
        return self._plugins

    def __repr__(self):
        return "Path: %s" % self.path

    plugins = property(get_plugins)

class PluginsPrefs(object):
    def __init__(self):
        self._paths = Prefs()['plugins.paths']
        self._plugins = Prefs()['plugins.enabled']

    def get_paths(self):
        val = self._paths.value
        return filter(None, val.split(os.pathsep))
    def get_plugins(self):
        val = self._plugins.value
        return filter(None, val.split(os.pathsep))

    def set_paths(self, value):
        self._paths.value = os.pathsep.join(value)
    def set_plugins(self, value):
        self._plugins.value = os.pathsep.join(value)

    def save_changes(self):
        # Not implemented all changes are saved automatically here
        pass

    paths = property(get_paths, set_paths)
    plugins = property(get_plugins, set_plugins)

class PluginEngine(Singleton):
    """
    Plugin Engine class
    """

    def __init__(self):
        """
        Initialize the engine with the paths were plugins are located

        @type paths tuple
        @param paths a tuple containing various directory where the plugins are
                     located
        """

        log.debug(">>> Initializing Plugin Engine")

        # Initialize our objects
        self.plugins = PluginsPrefs()
        self.tree = PluginsTree()
        self.core = Core()

        self.available_plugins = None
        self.paths = None

        self.apply_updates()
        self.recache()

    def apply_updates(self):
        """
        Check the downloaded plugins and move to the proper location
        """

        dest_dir = PM_PLUGINS_DIR
        temp_dir = PM_PLUGINS_TEMP_DIR
        down_dir = PM_PLUGINS_DOWNLOAD_DIR

        for file in os.listdir(temp_dir):
            try:
                os.remove(file)
            except Exception:
                continue

        for file in os.listdir(down_dir):
            path = os.path.join(down_dir, file)

            try:
                if not '.ump' in file:
                    os.remove(path)
                    continue

                fullname = file[:file.index('.ump') + 4]
                dst_name = os.path.join(dest_dir, fullname)

                if os.path.exists(dst_name):
                    os.remove(dst_name)

                log.debug("Installing new plugin from update: %s" % dst_name)

                os.rename(path, dst_name)

            except Exception, err:
                log.debug("Error in appply_updates(): %s" % err)
                continue

    def recache(self):
        """
        Reinit the available_plugins and paths fields
        """

        self.available_plugins = []
        self.paths = {}

        idx = 0
        for path in self.plugins.paths:
            plug_path = PluginPath(path)
            self.paths[path] = (idx, plug_path)

            self.available_plugins.extend(
                [v for k, v in plug_path.plugins.items()]
            )

            idx += 1

    def load_selected_plugins(self):
        """
        Load the selected plugins specified in config file
        """

        # Load the plugins in order (specified in conf file)
        for plugin in self.plugins.plugins:

            if not plugin or plugin == "":
                continue

            loaded, errmsg = self.load_plugin_from_path(plugin)

            if not loaded:
                log.warning(errmsg)

        # Check out the global variable PM_PLUGINS if we are in
        # development enviroment.

        if PM_DEVELOPMENT:
            plugins = os.getenv('PM_PLUGINS', '')

            if not plugins:
                return

            for plugin in plugins.split(os.pathsep):
                self.load_from_directory(plugin)

    def load_from_directory(self, path):
        log.debug("Loading source files from plugin directory: %s" % path)
        self.tree.load_directory(path)

    def load_plugin_from_path(self, plugin, force=False):
        """
        Load a plugin from a full path

        @param force True to not check plugin deps

        @return (True, None) if is ok OR
                (False, errmsg) if something went wrong
        """

        try:
            log.debug("Loading plugin %s" % plugin)

            path = os.path.dirname(plugin)
            file = os.path.basename(plugin)

            if not path in self.paths:
                # Not in path so we could remove from the list

                if plugin in self.plugins.plugins:
                    tmp = self.plugins.plugins
                    tmp.remove(plugin)
                    self.plugins.plugins = tmp

                return (False, "Plugin not in path (%s)" % plugin)

            d = self.paths[path][1].get_plugins()

            if file not in d:
                return (False, "Plugin does not exists anymore (%s)" % plugin)

            self.tree.load_plugin(d[file], force)

            # Setting enabled field for PluginReader to
            # mark a clean startup
            d[file].enabled = True

            # Save the changes
            path = d[file].get_path()
            lst = self.plugins.plugins

            if not path in lst:
                log.debug(">>> Appending plugin to conf file")
                lst.append(path)

                self.plugins.plugins = lst

            return (True, None)

        # return the exception class
        except PluginException, err:
            return (False, err)

    #
    # Used by PluginWindow
    #

    def load_plugin(self, reader, force=False):
        """
        Load a plugin

        @param reader a PluginReader
        @param force True to not check depends
        """
        return self.load_plugin_from_path(reader.get_path(), force)

    def unload_plugin(self, reader, force=False):
        """
        Unload a plugin

        @param reader a PluginReader
        @param force True to force unload phase
        """
        try:
            self.tree.unload_plugin(reader, force)

            path = reader.get_path()
            lst  = self.plugins.plugins

            if path in lst:
                log.debug(">>> Removing plugin from autoload")
                lst.remove(path)

                self.plugins.plugins = lst

            reader.enabled = False

            return (True, None)
        except PluginException, err:
            return (False, err)

    def uninstall_plugin(self, reader):
        """
        Low level uninstall procedure

        @param reader a PluginReader
        @return True if ok or False
        """

        try:
            os.remove(reader.get_path())
            self.recache()
            return True
        except Exception, err:
            log.warning("Error in uninstall_plugin(): %s" % err)
            return False
