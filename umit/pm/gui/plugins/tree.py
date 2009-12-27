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

sys.plugins_path = []

from umit.pm.core.i18n import _
from umit.pm.core.const import PM_DEVELOPMENT, PM_PLUGINS_TEMP_DIR
from umit.pm.core.atoms import generate_traceback
from umit.pm.core.logger import log
from umit.pm.gui.plugins.atoms import Version, DepDict
from umit.pm.gui.plugins.core import Core

from umit.pm.manager.auditmanager import PassiveAudit, ActiveAudit

from distutils.sysconfig import get_config_vars

import __builtin__
original_import = __builtin__.__import__

def hook_import(lib, globals=None, locals=None, fromlist=None, level=-1):
    try:
        return original_import(lib, globals, locals, fromlist, level)
    except ImportError, err:

        # This is a hacky fallback to permit loading of modules
        # with .so or .dll suffix inside .ump files

        # The .so/.dll libraries are extracted in a temp directory
        # that is cleaned on UMIT exit/start

        for reader in sys.plugins_path:
            path = os.path.join(PM_PLUGINS_TEMP_DIR,
                                lib.split('.')[-1] + get_config_vars("SO")[0])

            try:
                out = open(path, 'wb')

                out.write(reader.file.read(
                    'lib/%s%s' % (lib.replace(".", "/"),
                                  get_config_vars("SO")[0]))
                )
                out.close()
            except Exception, exc:
                continue

            path = os.path.dirname(out.name)
            name = os.path.basename(out.name)

            try:
                sys.path.insert(0, path)

                try:
                    return original_import(name.replace(
                               get_config_vars("SO")[0], ""), level=0)
                except Exception, exc:
                    continue
            finally:
                sys.path.pop(0)

        raise err

class Package(object):
    """
    It represents a Plugin object (used *ONLY FOR TESTING* purpose)
    """

    def __init__(self, name, n, p, c):
        self.name = name
        self.needs = n
        self.provides = p
        self.conflicts = c

    def __repr__(self):
        return self.name

class PluginException(Exception):
    def __init__(self, txt, summ):
        Exception.__init__(self, _("Unable to load %s") % txt)
        self.summary = summ

class PluginsTree(object):
    """
    Manages and tracks the loads/unloads of plugins objects
    """

    def __init__(self):
        """
        Create a new PluginsTree

        @param parent a PluginEngine instance
        """

        # A dict to trace plugin instances
        self.instances = {}
        self.modules = {}

        self.who_conflicts, \
            self.who_provides, \
            self.who_needs = DepDict(), DepDict(), DepDict()
        self.pkg_lst = list()

    def dump(self):
        log.info(">>> dump(): conflicts/provides/needs: %d / %d / %d" % \
              (
                  len(self.who_conflicts),
                  len(self.who_provides),
                  len(self.who_needs)
              )
        )

    def check_conflicts(self, pkg):
        """
        Check the conflicts between pkg and global list of provides or
        loaded plugins.

        The return list contains entry like:
            (phase-number:int,
                (p_name:str, p_op:Operator, p_ver:Version) -> Provider
                (c_name:str, c_op:Operator, c_ver:Version) -> Conflicter
            )

        @param pkg the plugin to check
        @return [] if everything is OK or a list of plugins
                conflicting with pkg
        """

        lst = []

        #
        # 1) We should check the cache conflicts agains pkg

        for provide in pkg.provides:
            try:
                name, op, ver = Version.extract_version(provide)

                if not name in self.who_conflicts:
                    continue

                for c_op, c_ver, c_pkg in self.who_conflicts[name]:

                    # We could have
                    # c_op, c_ver >=, 2.0.0
                    # ver = 3.0.0

                    # We could have a None if a conflict entry didn't provide
                    # any version or operator

                    if c_op.op_str == '.' or c_op(ver, c_ver) is True:
                        lst.append(
                            (1,
                             (name, op, ver),	# Provider
                             (c_pkg, c_op, c_ver)	# Conflicter
                             )
                        )
            except Exception, err:
                log.error(err)
                log.error("1) Ignoring conflict entry ...")

                continue

        #
        # 2) We should check the package conflicts against cache provides

        for conflict in pkg.conflicts:
            try:
                name, op, ver = Version.extract_version(conflict)

                if not name in self.who_provides:
                    continue

                # Only '=' operator presents:
                # providers['woot'] = [('=', '2.0', pkg1), ('=', '2.1', pkg2)]

                for p_op, p_ver, p_pkg in self.who_provides[name]:
                    # for example we could have
                    # name, op, ver = dummy, >=, 2.0.0
                    # p_ver = 2.0.3

                    # strict checking for avoid false results
                    # if None was returned
                    if op(p_ver, ver) is True:
                        # So we have a conflict. Just add to the list
                        lst.append(
                            (2,
                             (p_pkg, p_op, p_ver),   # Provider
                             (name, op, ver)	# Conflicter
                             )
                        )

            except Exception, err:
                log.error(err)
                log.error("2) Ignoring conflict entry ...")

                continue

        return lst

    def check_needs(self, pkg):
        """
        Check the needs between pkg and global list of provides.

        The return list contains entry like:
            (name:str, op:Operator, ver:Version) -> need not found

        @param pkg the plugin to check
        @return [] if everything is OK or a list of not resolved needs
        """

        # We have passed the conflict stage
        # so check for needs

        lst = []

        for need in pkg.needs:
            try:
                found = False
                name, op, ver = Version.extract_version(need)

                if not name in self.who_provides:
                    lst.append((name, op, ver))
                    continue

                for n_op, n_ver, n_pkg in self.who_provides[name]:
                    # for example we could have
                    # name, op, ver = dummy, >=, 2.0.0
                    # n_ver = 2.0.3

                    # TODO: check me
                    if op(n_ver, ver) is True or op(n_ver, ver) is None:
                        found = True
                        break

                # If we are here not applicable deps were found so add
                if not found:
                    lst.append((name, op, ver))

            except Exception, err:
                log.error(err)
                log.error("Ignoring need entry ...")

                continue

        return lst

    def add_plugin_to_cache(self, pkg):
        """
        Exports the needs/provides/conflicts to the global dicts
        """

        for attr in ('conflicts', 'provides', 'needs'):
            for dep in getattr(pkg, attr, []):
                try:
                    name, op, ver = Version.extract_version(dep)
                    d = getattr(self, "who_%s" % attr)
                    d[name] = (op, ver, pkg)
                except Exception, err:
                    log.warning(err)
                    log.warning("Ignoring %s entry" % dep)

        # Adds plugin to global list
        self.pkg_lst.append(pkg)

    def load_plugin(self, pkg, force=False):
        """
        Load a plugin

        @param pkg the plugin to load
        @param force if True no checks for deps will performed
        @return None or raise a PluginException
        """

        if pkg in self.pkg_lst:
            raise PluginException(pkg, _("Plugin already loaded."))

        if not force:

            # 1) Check for conflicts
            ret = self.check_conflicts(pkg)

            if ret:
                reasons = []
                for phase, (p_name, p_op, p_ver), (c_name, c_op, c_ver) in ret:
                    reasons.append( \
                        "-%d- Plugin '%s' provides %s which conflicts with " \
                        "%s conflict entry for plugin '%s'" % \
                        ( \
                            phase, pkg, \
                            Version.stringify_version(p_name, p_op, p_ver), \
                            Version.stringify_version(p_name, c_op, c_ver), \
                            c_name \
                        ) \
                    )

                raise PluginException(pkg, "\n".join(reasons))


            # 2) Check for needs
            ret = self.check_needs(pkg)

            if ret:
                reasons = []
                for (n_name, n_op, n_ver) in ret:
                    reasons.append( \
                        "-3- Plugin '%s' needs %s, which actually is not " \
                        "provided by any plugin." % \
                        ( \
                            pkg, \
                            Version.stringify_version(n_name, n_op, n_ver) \
                        ) \
                    )

                raise PluginException(pkg, "\n".join(reasons))

        self.__load_hook(pkg)

        # Export to cache
        self.add_plugin_to_cache(pkg)
        self.dump()

    def check_list_needs(self, pkg):
        """
        Check the needs from list against pkg

        @param pkg the plugin to check
        @return [] if everything is OK or a list of not used needs
                (name, op, version)
        """

        # Clone the list and drops out pkg
        lst = self.pkg_lst[:]
        lst.remove(pkg)

        conflicts_lst = []

        for provide in pkg.provides:
            p_name, p_op, p_ver = Version.extract_version(provide)

            for n_pkg in lst:
                for need in n_pkg.needs:
                    n_name, n_op, n_ver = Version.extract_version(need)

                    if n_name != p_name:
                        continue

                    # It's our need and we have a dep! :D
                    if n_op(p_ver, n_ver) is True:
                        conflicts_lst.append((n_pkg, n_op, n_ver))

        return conflicts_lst

    def remove_plugin_from_cache(self, pkg):
        for attr in ('conflicts', 'provides', 'needs'):
            for dep in getattr(pkg, attr, []):
                try:
                    name, op, ver = Version.extract_version(dep)
                    d = getattr(self, "who_%s" % attr)

                    # It's more probably that the entry is in the last

                    for i in xrange(len(d[name]) - 1, -1, -1):
                        _op, _ver, _pkg = d[name][i]

                        if pkg == _pkg and \
                           ver == _ver and \
                           op == _op:
                            del d[name][i]

                    # Remove unused keys.
                    if not d[name]:
                        del d[name]

                except Exception, err:
                    log.warning(err)
                    log.warning("Ignoring %s entry" % dep)

        # Remove plugin to global list
        self.pkg_lst.remove(pkg)

    def unload_plugin(self, pkg, force=False):
        """
        Unload a plugin
        @param pkg the plugin to unload
        @param force if False check the depends

        @return None or raise a PluginException
        """

        if pkg not in self.pkg_lst:
            raise Exception("Plugin not loaded.")

        if not force:

            # No conflict check here.
            # 1) We should check need's list against pkg

            ret = self.check_list_needs(pkg)

            if ret:
                reasons = []

                for i in ret:
                    reasons.append(
                        "Plugin %s requires %s" % \
                        (i[0], Version.stringify_version(pkg, i[1], i[2]))
                    )

                raise PluginException(pkg, "\n".join(reasons))

        self.__unload_hook(pkg)

        self.remove_plugin_from_cache(pkg)
        self.dump()

    def __cache_import(self, pkg):
        """
        Use try/except with this
        """

        if pkg in self.modules:
            return self.modules[pkg]
        else:

            try:
                __builtin__.__import__ = hook_import
                module = hook_import(pkg.start_file, level=0)
            finally:
                __builtin__.__import__ = original_import

            self.modules[pkg] = module

            return module

    def load_directory(self, modpath):
        if not PM_DEVELOPMENT:
            log.error("This method should not be called in release.")
            return

        start_file = 'main'

        log.warning("You are loading a plugin without checking for needs, " \
                    "provides or conflitcts")
        log.warning("* You have been warned! *")

        log.warning("Assuming `%s' as start file!" % start_file)

        # Load the plugin
        sys.path.insert(0, os.path.abspath(modpath))

        if start_file in sys.modules:
            sys.modules.pop(start_file)

        try:
            __builtin__.__import__ = hook_import
            module = hook_import(start_file, level=0)

            if hasattr(module, "__plugins__") and \
               isinstance(module.__plugins__, list):
                lst = module.__plugins__
                ret = []

                for plug in lst:
                    try:
                        if issubclass(plug, PassiveAudit):
                            is_audit = 1
                        elif issubclass(plug, ActiveAudit):
                            is_audit = 2
                        else:
                            is_audit = 0

                        inst = plug()
                        inst.start(None)

                        if is_audit:
                            inst.register_decoders()
                            inst.register_hooks()

                        ret.append(inst)
                    except Exception, err:
                        log.critical("Error while starting %s:" % (plug))
                        log.critical(generate_traceback())
                        log.critical("Ignoring instance.")

                if not ret:
                    log.error("Not startable plugin defined in main file")
            else:
                log.error("No Plugin subclass")
        finally:
            __builtin__.__import__ = original_import

    def __load_hook(self, pkg):
        """
        This is the real load procedure of plugin.
        We'll use zipmodule to import and a global function expose
        to provide a simple method to access files inside the zip file
        to plugin.

        Raise a PluginException on fail

        @return None or raise a PluginException
        """

        if pkg in self.instances:
            raise PluginException(pkg, "Already present")

        # We need to get the start-file field from pkg and then try
        # to import it

        modpath = os.path.join(pkg.get_path(), 'lib')
        sys.path.insert(0, os.path.abspath(modpath))

        # This were removed
        fname = os.path.join(pkg.get_path(), 'bin', pkg.start_file)
        sys.path.insert(0, os.path.abspath(os.path.dirname(fname)))

        if pkg.start_file in sys.modules:
            sys.modules.pop(pkg.start_file)

        try:
            try:
                # We add to modules to avoid deleting and stop working plugin ;)
                sys.plugins_path.insert(0, pkg)
                module = self.__cache_import(pkg)

            except Exception, err:
                sys.plugins_path.pop(0)
                raise PluginException(pkg, str(err))

        finally:
            # Check that
            sys.path.pop(0)

        if hasattr(module, "__plugins__") and \
           isinstance(module.__plugins__, list):
            lst = module.__plugins__
            ret = []

            for plug in lst:
                try:

                    if issubclass(plug, PassiveAudit):
                        is_audit = 1
                    elif issubclass(plug, ActiveAudit):
                        is_audit = 2
                    else:
                        is_audit = 0

                    inst = plug()
                    inst.start(pkg)

                    if is_audit:
                        inst.register_decoders()
                        inst.register_hooks()

                    ret.append(inst)
                except Exception, err:
                    log.critical("Error while starting %s from %s:" % (plug,
                                                                       pkg))
                    log.critical(generate_traceback())
                    log.critical("Ignoring instance.")

            if not ret:
                raise PluginException(pkg, \
                              "No startablePlugin subclass in %s" % pkg)

            self.instances[pkg] = ret
        else:
            raise PluginException(pkg, "No Plugin subclass in %s" % pkg)

    def __unload_hook(self, pkg):
        """
        This is the real unload procedure of plugin.
        Raise a PluginException on fail

        @return None or raise a PluginException
        """

        if not pkg in self.instances:
            raise PluginException(pkg, "Already unloaded")

        for inst in self.instances[pkg]:
            try:
                inst.stop()
            except Exception, err:
                log.critical("Error while stopping %s from %s:" % (inst, pkg))
                log.critical(generate_traceback())
                log.critical("Ignoring instance.")

        try:
            sys.plugins_path.remove(pkg)

            if pkg.start_file in sys.modules:
                sys.modules.pop(pkg.start_file)

        except Exception:
            pass

        del self.instances[pkg]
        del self.modules[pkg]

    #
    # Usefull functions
    #

    def show_preferences(self, pkg):
        """
        Show the preference dialog if it's setted

        We use the field __pref_func__

        @param pkg a PluginReader
        @return True if it's defined and launched or
                False if it's not defined
        """

        pref_func = None

        try:
            module = self.__cache_import(pkg)
            pref_func = module.__pref_func__
        except Exception:
            pass

        # Instead using types
        def t(): pass

        if isinstance(pref_func, type(t)):
            pref_func()
            return True

        return False

    def show_about(self, pkg):
        """
        Show an about dialog for plugin.

        We use a field __about__
        """

        about_func = None

        try:
            module = self.__cache_import(pkg)
            about_func = module.__about__
        except Exception:
            pass

        # Instead using types
        def t(): pass

        if isinstance(about_func, type(t)):
            about_func()
        else:
            d = Core().about_dialog(pkg)

            d.run()
            d.hide()
            d.destroy()

    def get_provide(self, need, lst_need, need_module=False):
        """
        Get the requested package (used by Core)

        @param need is the dependency name
        @lst_need a list of (op, ver, name) that is the requirement for need
        """

        if not need in self.who_provides:
            return None

        ret = [(ver, pkg) for op, ver, pkg in self.who_provides[need]]

        # 1) create the list
        for p_op, p_ver, p_pkg in self.who_provides[need]:
            # p_op, p_ver, p_pkg = =, 2.0, dummy

            for op, ver, name in lst_need:
                # op, ver, name = >, 1.0, dummy

                # TODO: check that
                if op(p_ver, ver) == False and (p_ver, p_pkg) in ret:
                    print need, lst_need
                    print op, p_ver, ver
                    print p_ver, p_pkg
                    ret.remove((p_ver, p_pkg))

        # 2) Choose the better version (major)
        def compare(x, y):
            return x[0].__cmp__(y[0])

        ret.sort(compare)

        if not ret:
            return None
        else:
            if need_module:
                return self.modules[ret[0][1]]
            else:
                return self.instances[ret[0][1]]

def _test():
    """
    >>> 1
    1
    >>> dummy = Package('dummy', [], ['dummy-2.1'], ['woot'])
    >>> woot = Package('woot', ['>dummy-2.0'], ['=woot-2.0.0'], [])
    >>> conflicter = Package('conflicter', [], [], ['!dummy-2.0'])
    >>> tree = PluginsTree()

    >>> tree.load_plugin(conflicter)
    Succesfully loaded conflicter ;-)
    c/p/n: 1 / 0 / 0
    True

    >>> tree.load_plugin(dummy)
    -1- Plugin 'dummy' provides =dummy-2.1.0 which conflicts with !dummy-2.0.0 conflict entry for plugin 'conflicter'
    Unable to load dummy :(
    False

    >>> tree.load_plugin(Package('dummy', [], ['dummy-2.0'], []))
    Succesfully loaded dummy ;-)
    c/p/n: 1 / 1 / 0
    True

    >>> tree.unload_plugin(conflicter)
    Succesfully unloaded conflicter
    c/p/n: 0 / 1 / 0
    True

    >>> tree.load_plugin(woot)
    -3- Plugin 'woot' needs >dummy-2.0.0, which actually is not provided by any plugin.
    Unable to load woot :(
    False

    >>> tree.load_plugin(dummy)
    Succesfully loaded dummy ;-)
    c/p/n: 1 / 1 / 0
    True

    >>> tree.load_plugin(woot)
    -1- Plugin 'woot' provides =woot-2.0.0 which conflicts with woot-* conflict entry for plugin 'dummy'
    Unable to load woot :(
    False

    >>> tree.unload_plugin(dummy)
    Succesfully unloaded dummy
    c/p/n: 0 / 1 / 0
    True

    >>> tree.load_plugin(Package('woot', ['>=dummy-2.0'], [], []))
    Succesfully loaded woot ;-)
    c/p/n: 0 / 1 / 1
    True

    """

    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
