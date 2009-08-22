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
import gtk
import gobject

from umit.pm.core.i18n import _
from umit.pm.core.logger import log

from umit.pm.higwidgets.higbuttons import HIGButton
from umit.pm.higwidgets.higdialogs import HIGAlertDialog
from umit.pm.higwidgets.higrichlists import HIGRichList, PluginRow

from umit.pm.gui.plugins.core import Core
from umit.pm.gui.plugins.atoms import Version
from umit.pm.gui.plugins.update import FILE_GETTING, FILE_CHECKING, \
                                  FILE_ERROR, LATEST_GETTED, \
                                  LATEST_ERROR, LATEST_GETTING

from umit.pm.core.const import PIXMAPS_DIR


class PluginPage(gtk.VBox):
    def __init__(self, parent):
        gtk.VBox.__init__(self, False, 2)

        self.p_window = parent
        self.menu_enabled = True

        self.__create_widgets()
        self.__pack_widgets()

        self.install_updates_btn.hide()

    def __create_widgets(self):
        self.set_spacing(4)

        self.richlist = HIGRichList()

        self.hbbox = gtk.HButtonBox()
        self.hbbox.set_layout(gtk.BUTTONBOX_END)

        self.find_updates_btn = \
            HIGButton(_('Find updates'), gtk.STOCK_REFRESH)
        self.install_updates_btn = \
            HIGButton(_('Install updates'), gtk.STOCK_APPLY)
        self.skip_install_btn = \
            HIGButton(_('Skip'), gtk.STOCK_CANCEL)
        self.restart_btn = \
            HIGButton(_('Restart PacketManipulator'), gtk.STOCK_REFRESH)

    def __pack_widgets(self):
        self.hbbox.pack_start(self.find_updates_btn)
        self.hbbox.pack_start(self.skip_install_btn)
        self.hbbox.pack_start(self.install_updates_btn)
        self.hbbox.pack_start(self.restart_btn)

        self.pack_start(self.richlist)
        self.pack_start(self.hbbox, False, False, 0)

        self.find_updates_btn.connect('clicked', self.__on_find_updates)
        self.install_updates_btn.connect('clicked', self.__on_install_updates)
        self.skip_install_btn.connect('clicked', self.__on_skip_updates)
        self.restart_btn.connect('clicked', self.__on_restart)

        self.show_all()

    def clear(self, include_loaded=True):
        if include_loaded:
            self.richlist.clear()
            return

        def remove(row, richlist):
            if not row.reader.enabled:
                richlist.remove_row(row)

        self.richlist.foreach(remove, self.richlist)
        return self.richlist.get_rows()

    def populate(self):
        "Populate the richlist using available_plugins field"

        # We need a list of present plugin row to check for dup
        presents = []

        def add_to_list(row, list):
            list.append(row)

        self.richlist.foreach(add_to_list, presents)

        warn_reboot = False

        # We have to load available_plugins from engine
        for reader in self.p_window.engine.available_plugins:

            if reader.audit_type != -1:
                continue

            # Check if it's already present then remove the original
            # and add the new in case something is getting update.
            row = PluginRow(self.richlist, reader)

            for old in presents:
                # FIXME? we need to check also for version equality
                # and if are different just ignore the addition and
                # continue with the loop
                if old.reader.get_path() == row.reader.get_path():
                    self.richlist.remove_row(old)
                    row.enabled = True
                    warn_reboot = True

            # Connect the various buttons
            row.action_btn.connect('clicked', self.__on_row_action, row)
            row.uninstall_btn.connect('clicked', self.__on_row_uninstall, row)
            row.preference_btn.connect('clicked', self.__on_row_preference, row)

            row.connect('clicked', self.__on_row_preference, row)
            row.connect('popup', self.__on_row_popup)

            self.richlist.append_row(row)

        if warn_reboot:
            # Warn the user
            self.p_window.animated_bar.label = \
                _('Remember that you have to restart PacketManipulator to make '
                  'new version of plugins to be loaded correctly.')
            self.p_window.animated_bar.start_animation(True)

    def __on_restart(self, widget):
        "Called when the user click on the restart button"

        Core().mainwindow.emit('delete-event', None)

    def __on_skip_updates(self, widget):
        "Called when the user click on the skip button"

        # We need to repopulate the tree
        self.richlist.clear()
        self.populate()

        self.p_window.toolbar.unset_status()

        if self.restart_btn.flags() & gtk.VISIBLE:
            # That callback is called from a self.___on_install_updates

            self.restart_btn.hide()
            self.p_window.animated_bar.label = \
                _('Rembember to restart PacketManipulator to use new version '
                  'of plugins.')

        else:
            self.p_window.animated_bar.label = \
                    _('Update skipped')

        self.p_window.animated_bar.start_animation(True)

        self.skip_install_btn.hide()
        self.install_updates_btn.hide()
        self.find_updates_btn.show()

        self.menu_enabled = True

    def __on_install_updates(self, widget):
        """
        Called when the user click on 'install updates' button

        This function call the start_download() of UpdateEngine
        and then add a timeout callback (__refresh_row_download) to
        update the gui at interval of 300 milliseconds.
        """

        lst = []
        for obj in self.p_window.update_eng.list:
            if obj.status != LATEST_GETTED:
                self.richlist.remove_row(obj.object)
                continue

            if obj.object.show_include:
                lst.append(obj)

            obj.object.show_include = False

            # Reset indexes
            obj.last_update_idx = 0
            obj.selected_update_idx = \
                obj.object.versions_button.get_active() - 1

        self.install_updates_btn.set_sensitive(False)
        self.skip_install_btn.set_sensitive(False)

        self.p_window.update_eng.list = lst
        self.p_window.update_eng.start_download()

        self.p_window.toolbar.show_message( \
            _("<b>Downloading updates ...</b>"), \
            file=os.path.join(PIXMAPS_DIR, "Throbber.gif") \
        )
        gobject.timeout_add(300, self.__refresh_row_download)

    def __refresh_row_download(self):
        """
        This is the timeout callback called to update the gui
        in the download phase (the last)
        """

        working = False

        for obj in self.p_window.update_eng.list:
            obj.lock.acquire()

            try:
                if obj.status == FILE_GETTING or \
                   obj.status == FILE_CHECKING:
                    working = True

                row = obj.object
                row.message = obj.label
                row.progress = obj.fract
            finally:
                obj.lock.release()

        if not working:

            errors = ''

            for obj in self.p_window.update_eng.list:
                row = obj.object
                row.message = obj.label
                row.progress = None

                if not errors and obj.status == FILE_ERROR:
                    errors = ' but with <b>some errors</b>'

            # Only warn the user about changes take effects on restart
            # on restart just move the plugins stored in home directory
            # in the proper location

            self.p_window.animated_bar.label = \
                _('Update phase complete%s. Now restart ' \
                  'PacketManipulator to changes make effects.') % errors
            self.p_window.animated_bar.start_animation(True)

            self.p_window.toolbar.unset_status()

            self.install_updates_btn.hide()

            # Let the user to choose to restart or not PacketManipulator
            self.skip_install_btn.set_sensitive(True)

            self.restart_btn.show()

        return working

    def __on_find_updates(self, widget):
        """
        Called when the user click on 'find updates' button

        This function call the start_update() of UpdateEngine
        and then add a timeout callback (__update_rich_list) to
        update the gui at interval of 300 milliseconds.
        """

        # First add audits to the list
        presents = []

        def add_to_list(row, list):
            list.append(row)

        self.richlist.foreach(add_to_list, presents)

        warn_reboot = False

        # We have to load available_plugins from engine
        for reader in self.p_window.engine.available_plugins:

            if reader.audit_type == -1:
                continue

            # Check if it's already present then remove the original
            # and add the new in case something is getting update.
            row = PluginRow(self.richlist, reader)

            for old in presents:
                # FIXME? we need to check also for version equality
                # and if are different just ignore the addition and
                # continue with the loop
                if old.reader.get_path() == row.reader.get_path():
                    self.richlist.remove_row(old)
                    row.enabled = True
                    warn_reboot = True

            # Connect the various buttons
            row.action_btn.connect('clicked', self.__on_row_action, row)
            row.uninstall_btn.connect('clicked', self.__on_row_uninstall, row)
            row.preference_btn.connect('clicked', self.__on_row_preference, row)

            row.connect('clicked', self.__on_row_preference, row)
            row.connect('popup', self.__on_row_popup)

            self.richlist.append_row(row)

        # Then goes with the update

        self.find_updates_btn.set_sensitive(False)
        self.menu_enabled = False

        lst = []

        def append(row, lst):
            if row.reader.update:
                row.message = _("Waiting ...")
                row.activatable = False
                row.enabled = True
                lst.append(row)
            else:
                self.richlist.remove_row(row)

        self.richlist.foreach(append, lst)

        if not lst:
            self.p_window.toolbar.unset_status()

            self.p_window.animated_bar.label = \
                _("No plugins provide an update URL. Cannot proceed.")
            self.p_window.animated_bar.image = gtk.STOCK_DIALOG_ERROR
            self.p_window.animated_bar.start_animation(True)

            self.p_window.update_eng.updating = False
            self.find_updates_btn.set_sensitive(True)
            self.menu_enabled = True

            self.richlist.clear()
            self.populate()
            return

        # We can now begin the update phase, so warn the user.

        self.p_window.toolbar.show_message( \
            _("<b>Looking for %d updates ...</b>") % len(lst), \
            file=os.path.join(PIXMAPS_DIR, "Throbber.gif") \
        )

        self.p_window.update_eng.list = lst
        self.p_window.update_eng.start_update()

        # Add a timeout function to update label
        gobject.timeout_add(300, self.__update_rich_list)

    def __query_tooltip_versions_button(self, widget, x, y, keyboard_tip, \
                                        tooltip, obj):

        idx = obj.object.versions_button.get_active() - 1

        if idx >= 0:
            desc = obj.updates[idx].description

            if desc:
                tooltip.set_markup(desc)
                tooltip.set_icon_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_MENU)
                return True

        return False

    def __update_rich_list(self):
        """
        This is the timeout callback called to update the gui
        in the find phase
        """

        working = False

        for upd_obj in self.p_window.update_eng.list:
            upd_obj.lock.acquire()

            try:
                # Check if we are working
                if upd_obj.status == LATEST_GETTING:
                    working = True

                # Update the row
                row = upd_obj.object
                row.message = upd_obj.label
            finally:
                upd_obj.lock.release()

        # No locking from here we have finished

        if not working:
            # Mark as finished
            self.p_window.update_eng.stop()
            self.find_updates_btn.set_sensitive(True)

            lst = filter( \
                lambda x: (x.status == LATEST_GETTED) and (x) or (None),\
                self.p_window.update_eng.list \
            )
            elst = filter( \
                lambda x: (x.status == LATEST_ERROR) and (x) or (None),\
                self.p_window.update_eng.list \
            )

            if not lst and not elst:
                self.p_window.toolbar.unset_status()

                self.p_window.animated_bar.label = \
                    _('<b>No updates found</b>')
                self.p_window.animated_bar.start_animation(True)

                self.richlist.clear()
                self.populate()

                self.menu_enabled = True
            else:
                # Now prepare the download page

                if not elst:
                    self.p_window.toolbar.show_message( \
                        _("<b>Updates found: %d</b>") % len(lst), \
                        stock=gtk.STOCK_APPLY \
                    )
                else:
                    self.p_window.toolbar.show_message( \
                        _('<b>Updates found: %d with %d errors</b>')  \
                        % (len(lst), len(elst)), stock=gtk.STOCK_APPLY \
                    )

                for obj in self.p_window.update_eng.list:
                    row = obj.object
                    active = (obj.status == LATEST_GETTED)

                    if active:
                        obj.last_update_idx = 0
                        row.show_include = True

                        log.debug("Connecting 'query-tooltip' for %s" % obj)

                        # The tooltip is showed and hidden continuously
                        row.versions_button.props.has_tooltip = True
                        row.versions_button.connect(
                            'query-tooltip',
                            self.__query_tooltip_versions_button, obj
                        )

                        row.versions_model.clear()

                        row.versions_model.append([
                            gtk.STOCK_CANCEL, _("Skip")
                        ])

                        for update in obj.updates:
                            cur_v = Version(row.reader.version)
                            new_v = Version(update.version)

                            if new_v > cur_v:
                                row.versions_model.append([
                                    gtk.STOCK_GO_UP, _("Update to %s") % \
                                    update.version
                                ])
                            elif new_v == cur_v:
                                row.versions_model.append([
                                    gtk.STOCK_REFRESH, _("Reinstall %s") % \
                                    update.version
                                ])
                            else:
                                row.versions_model.append([
                                    gtk.STOCK_GO_DOWN, _("Downgrade to %s") % \
                                    update.version
                                ])

                        row.versions_button.set_active(0)
                        row.message = obj.label
                    else:
                        row.saturate = True

                if lst:
                    self.install_updates_btn.show()

                self.find_updates_btn.hide()
                self.skip_install_btn.show()

        return working

    def __on_row_popup(self, row, evt):
        "Popup menu"

        if not self.menu_enabled or not row.activatable:
            return

        menu = gtk.Menu()

        stocks = (
            gtk.STOCK_PREFERENCES,
            gtk.STOCK_HOME,
            gtk.STOCK_ABOUT,
            None,
            (gtk.STOCK_MEDIA_PLAY, gtk.STOCK_MEDIA_STOP),
            gtk.STOCK_CLEAR
        )

        labels = (
            _('<b>Preferences</b>'),
            _('Visit homepage'),
            _('About %s') % row.reader.name,
            None,
            (_('Enable'), _('Disable')),
            _('Uninstall')
        )

        callbacks = (
            self.__on_row_preference,
            self.__on_row_homepage,
            self.__on_row_about,
            None,
            self.__on_row_action,
            self.__on_row_uninstall
        )

        for stock, label, cb in zip(stocks, labels, callbacks):
            if not label:
                menu.append(gtk.SeparatorMenuItem())
                continue

            # Get the right stock, label choosing from the row state
            if isinstance(label, tuple):
                if row.enabled:
                    stock, label = stock[1], label[1]
                else:
                    stock, label = stock[0], label[0]


            act = gtk.Action(None, label, '', stock)

            item = act.create_menu_item()
            item.get_child().set_use_markup(True)
            item.connect('activate', cb, row)

            menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, evt.button, evt.time)

    def __on_row_action(self, widget, row):
        "Enable/Disable menu/button callback"

        if not row.enabled:
            func = self.p_window.engine.load_plugin
        else:
            func = self.p_window.engine.unload_plugin

        ret, errmsg = func(row.reader)

        if not ret:
            dialog = HIGAlertDialog(
                self.p_window,
                gtk.DIALOG_MODAL,
                gtk.MESSAGE_ERROR,
                message_format=errmsg,
                secondary_text=errmsg.summary
            )
            dialog.run()
            dialog.destroy()
        else:
            row.enabled = not row.enabled

    def __on_row_uninstall(self, widget, row):
        "Uninstall button callback"

        # If it's enabled we must disable and then disinstall

        def dialog(txt, sec):
            return HIGAlertDialog(self.p_window, 0, gtk.MESSAGE_QUESTION, \
                gtk.BUTTONS_YES_NO, txt, sec)

        if row.enabled:
            d = dialog( \
                _('Disabling Plugin'), \
                _('Do you want to disable %s plugin?') % row.reader.name \
            )

            r = d.run()
            d.hide()
            d.destroy()

            if r == gtk.RESPONSE_YES:
                r, err = self.p_window.engine.unload_plugin(row.reader)

                if not r:
                    d = dialog( \
                        _('Can not disable Plugin'), \
                        _('%s\nDo you want to force '
                          'the unload phase for %s plugin?') % \
                            (err.summary, row.reader.name) \
                    )

                    r = d.run()
                    d.hide()
                    d.destroy()

                    if r == gtk.RESPONSE_YES:
                        self.p_window.engine.unload_plugin(row.reader, True)
                        self.__uninstall(row)
                else:
                    self.__uninstall(row)
        else:
            self.__uninstall(row)

    def __uninstall(self, row):
        "Uninstall semi-low level function"

        row.activatable = False

        if self.p_window.engine.uninstall_plugin(row.reader):
            del row
            self.richlist.clear()
            self.p_window.plug_page.populate()
        else:
            row.activatable = True

            self.p_window.animated_bar.label = \
                _('Unable to uninstall %s plugin.') % row.reader
            self.p_window.animated_bar.start_animation(True)

    def __on_row_preference(self, widget, row):
        "Preference button callback"

        if not self.p_window.engine.tree.show_preferences(row.reader):
            self.p_window.animated_bar.label = \
                _('No preferences for %s') % row.reader.name
            self.p_window.animated_bar.start_animation(True)

    def __on_row_about(self, widget, row):
        "About menu callback"
        self.p_window.engine.tree.show_about(row.reader)

    def __on_row_homepage(self, widget, row):
        "Homepage menu callback"
        Core().open_url(row.reader.url)
