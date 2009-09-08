#!/usr/bin/env python

#------------------------------------------------------------------------------
#
#   Copyright (c) 1998 James Henstridge, 2006 Nicolas Rougier
# 
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
# 
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#   Copyright (c) 2008 Francesco Piccinno
#   
#   Readapting for UMIT use and implemented a completion engine ripped off
#   from pyconsole.py. These parts are copyrighted by respective authors:
#
#   Copyright (C) 2004-2005 by Yevgen Muntyan <muntyan@math.tamu.edu>
#------------------------------------------------------------------------------


""" Interactive GTK console

This console is heavily based on the GTK Interactive Console bundled with
The Gimp and implements an interactive python session in a GTK window. 

Shortcuts:
----------
    Ctrl-A : go to line start
    Ctrl-E : go to line end
    Ctrl-K : clear line from cursor to end
    Ctrl-L : clear
"""

__version__ = '1.0'
__author__  = 'Nicolas Rougier'
__email__   = 'Nicolas.Rougier@loria.fr'


import sys
import traceback
import os, os.path

# UI stuff
import pygtk

import gtk
import pango
import gobject

# Completions stuff
import re
import rlcompleter

from umit.pm.core.i18n import _

stdout = sys.stdout
if not hasattr(sys, 'ps1'): sys.ps1 = '(PM) '
if not hasattr(sys, 'ps2'): sys.ps2 = ' ... '
 
_orig = os.write 
 
def _hook(f, txt): 
    if f == 1: 
        sys.stdout.write(txt) 
    else: 
        _orig.write(f, txt) 
 
os.write = _hook 

PSLEN = len(sys.ps1)

# =============================================================================
class gtkoutfile:
    """
    A fake output file object.  It sends output to a GTK TextView widget,
    and if asked for a file number, returns one set on instance creation
    """
    
    def __init__(self, console, fn, font):
        self.fn = fn
        self.console = console
        #self.__b = w.get_buffer()
        #self.__ins = self.__b.get_mark('insert')
        self.font = font
    def close(self): pass
    flush = close
    def fileno(self):    return self.fn
    def isatty(self):    return False
    def read(self, a):   return ''
    def readline(self):  return ''
    def readlines(self): return []
    def write(self, s):
        self.console.write (s, self.font)
    def writelines(self, l):
        for s in l:
            self.console.write (s, self.font)
    def seek(self, a):   raise IOError, (29, 'Illegal seek')
    def tell(self):      raise IOError, (29, 'Illegal seek')
    truncate = tell


# =============================================================================
class gtkinfile:
    """
    A fake input file object.  It receives input from a GTK TextView widget,
    and if asked for a file number, returns one set on instance creation
    """
    
    def __init__(self, console, fn):
        self.fn = fn
        self.console = console
    def close(self): pass
    flush = close
    def fileno(self):    return self.fn
    def isatty(self):    return False
    def read(self, a):   return self.readline()
    def readline(self):
        self.console.input_mode = True
        while self.console.input_mode:
            while gtk.events_pending():
                gtk.main_iteration()
        s = self.console.input
        self.console.input = ''
        return s+'\n'
    def readlines(self): return []
    def write(self, s):  return None
    def writelines(self, l): return None
    def seek(self, a):   raise IOError, (29, 'Illegal seek')
    def tell(self):      raise IOError, (29, 'Illegal seek')
    truncate = tell


# =============================================================================
class History:
    """ Basic command history class
    """
    
    def __init__ (self):
        """ Initializes history """
        
        self.history = ['']
        self.position = len (self.history)-1
        
    def prev (self, current):
        """ Get previous command in history """
        
        if self.position > 0:
            l = current
            if len(l) > 0 and l[0] == '\n': l = l[1:]
            if len(l) > 0 and l[-1] == '\n': l = l[:-1]
            if self.position > 0:
                if self.position == (len(self.history)-1):
                    self.history[len(self.history)-1] = l
                self.position = self.position - 1
                return self.history[self.position]
        return current
        
    def next (self, current):
        """ Get next command in history """
        
        if self.position < len(self.history) - 1:
            self.position = self.position + 1
            return self.history[self.position]
        return current
    
    def append (self, line):
        """ Append a new command to history """
        
        self.position = len(self.history) - 1
        if not len(line):
            return
        if ((self.position == 0) or (self.position > 0 and 
                        line != self.history[self.position-1])):
            self.history[self.position] = line
            self.position = self.position + 1
            self.history.append('')
    
    def open (self, filename):
        """ Open an history file """
        
        file = open (filename)
        self.history = []
        for l in file:
            self.history.append(l[:-1])
        self.history.append('')
        self.position = len(self.history)-1
        file.close()

    def save (self, filename):
        """ Save history to a file """
        
        file = open (filename, 'w')
        for l in self.history:
            if len(l) > 0:
                file.write(l+'\n')
        file.close()
        
    def __repr__(self):
        """ History representation """
        
        return self.history.__repr__()


# =============================================================================
def commonprefix(m):
    "Given a list of pathnames, returns the longest common leading component"
    if not m: return ''
    prefix = m[0]
    for item in m:
        for i in range(len(prefix)):
            if prefix[:i+1] != item[:i+1]:
                prefix = prefix[:i]
                if i == 0:
                    return ''
                break
    return prefix


# =============================================================================
class Console (gtk.ScrolledWindow):
    """ Interactive GTK console class """

    __gsignals__ = {
        'eval' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN, (gobject.TYPE_STRING, ))
    }

    def __init__(self, namespace={}, quit_handler = None):
        """ Initialize console
        """
        
        # Setup scrolled window
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type (gtk.SHADOW_ETCHED_IN)
        self.set_border_width(0)

        # Setup text view
        self.text = gtk.TextView ()
        self.text.set_property ('can-focus', True)
        self.text.modify_font (pango.FontDescription("mono 9"))
        self.text.set_editable (True)
        self.text.set_wrap_mode(True)
        self.text.set_left_margin(1)
        self.text.set_right_margin(1)
        self.text.set_size_request(0, 0)
        
        # Setup text buffer
        self.buffer = self.text.get_buffer ()
        self.buffer.create_tag ('prompt', \
                weight=pango.WEIGHT_BOLD, editable=False)
        self.buffer.create_tag ('script', \
                foreground='darkgrey', style=pango.STYLE_OBLIQUE, \
                editable=False)
        self.buffer.create_tag ('normal', \
                foreground='blue', editable=False)
        self.buffer.create_tag ('error', \
                foreground='red', style=pango.STYLE_OBLIQUE, \
                editable=False)
        self.buffer.create_tag ('extern', \
                foreground='brown', weight=pango.WEIGHT_BOLD, \
                editable=False)
        self.buffer.create_tag ('center', \
                justification=gtk.JUSTIFY_CENTER, editable=False)
        
        # Setup event handlers
        self.text.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.text.connect ('key-press-event', self.on_key_pressed)
        self.text.connect ('button-release-event', self.on_button_released)
        self.text.connect ('drag-data-received', self.on_drag_data_received)
        self.add(self.text)
        
        # Internal setup
        self.tab_pressed = 0
        self.nonword_re = re.compile("[^\w\._]")
        self.completer = rlcompleter.Completer()
        self.namespace = namespace
        self.cmd = ''
        self.input = ''
        self.input_mode = False
        self.linestart = 0
        self.quit_handler = self.quit
        if quit_handler:
            self.quit_handler = quit_handler

        # Setup hooks for standard output.
        self.stdout = gtkoutfile(self, self.__get_stream(sys.stdout), 'normal')
        self.stderr = gtkoutfile(self, self.__get_stream(sys.stderr), 'error')
        self.stdin  = gtkinfile(self, self.__get_stream(sys.stdin))
        

        # Setup command history
        self.history = History()
        self.namespace['__history__'] = self.history
        self.show_all()
        
    def __get_stream(self, stream): 
        if hasattr(stream, 'fileno'): 
            return stream.fileno() 
        elif hasattr(stream, '_file') and hasattr(stream._file, 'fileno'): 
            return stream._file.fileno() 
        else: 
            return stream 

    def on_button_released(self, widget, event):
        """ Text selection a la mIRC """
        ret = self.buffer.get_selection_bounds()

        if ret:
            start, end = ret
            gtk.clipboard_get().set_text(self.buffer.get_text(start, end, True))
            self.buffer.place_cursor(end)

    def complete(self, txt):
        """ Tab completion stuff """
        start = ''
        word = txt
        nonwords = self.nonword_re.findall(txt)

        if nonwords:
            last = txt.rfind(nonwords[-1]) + len(nonwords[-1])
            start = txt[:last]
            word = txt[last:]

        if not word:
            return

        i = 0
        ret = []

        while True:
            try:
                s = self.completer.complete(word, i)
                if s:
                    ret.append(s)
                    i += 1
                else:
                    ret.sort()
                    break
            except Exception:
                return

        if ret:
            prefix = commonprefix(ret)
            if prefix != word:
                start_it = self.buffer.get_iter_at_offset(self.linestart)
                start_it.forward_chars(len(start))

                end_it = start_it.copy()
                end_it.forward_chars(len(word))

                self.buffer.delete(start_it, end_it)
                self.buffer.insert(end_it, prefix)

            elif self.tab_pressed > 1:
                self.print_completions(ret)
                self.tab_pressed = 0

    def get_width(self):
        """ Dummy method to return the width of window """

        if not (self.flags() & gtk.REALIZED):
            return 80

        layout = pango.Layout(self.get_pango_context())
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        layout.set_text(letters)
        pix_width = layout.get_pixel_size()[0]
        return self.allocation.width * len(letters) / pix_width

    def print_completions(self, completions):
        """ Print completions """

        text = self.current_line()

        iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        self.buffer.insert_with_tags_by_name(iter, '\n', 'normal')

        width = max(self.get_width(), 4)
        max_width = max([len(s) for s in completions])
        n_columns = max(int(width / (max_width + 1)), 1)
        col_width = int(width / n_columns)
        total = len(completions)
        col_length = total / n_columns

        if total % n_columns:
            col_length = col_length + 1
        col_length = max(col_length, 1)

        if col_length == 1:
            n_columns = total
            col_width = width / total

        for i in range(col_length):
            for j in range(n_columns):
                ind = i + j*col_length
                if ind < total:
                    if j == n_columns - 1:
                        n_spaces = 0
                    else:
                        n_spaces = col_width - len(completions[ind])
                    self.buffer.insert_with_tags_by_name( \
                            iter, completions[ind] + " " * n_spaces, 'normal')
            self.buffer.insert_with_tags_by_name(iter, '\n', 'normal')

        self.write (self.prompt, 'prompt')
        self.replace(text)

    def banner(self):
        """ Display python banner """
        
        iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        self.buffer.insert_with_tags_by_name(iter,
                _('Welcome to PacketManipulator Python Shell (running on %s)\n') % os.name,
                'center', 'extern'
        )
        iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        self.buffer.insert_with_tags_by_name(iter, 
            _('Please be carefull becouse you are in the PM main loop\n'),
            'center', 'script'
        )
        self.text.scroll_to_mark (self.buffer.get_insert(), 0)
        self.prompt1()

    def append_text(self, txt):
        iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        self.buffer.insert_with_tags_by_name(iter, txt, 'normal')
        self.text.scroll_to_mark (self.buffer.get_insert(), 0)

    def prompt1 (self):
        """ Display normal prompt """
        
        self.prompt = sys.ps1
        self.write (self.prompt, 'prompt')


    def prompt2 (self):
        """ Display continuation prompt """
        
        self.prompt = sys.ps2
        self.write (self.prompt, 'prompt')


    def clear (self):
        """ Clear text buffer & view """
        
        line = self.current_line()
        self.buffer.delete (self.buffer.get_start_iter(), self.buffer.get_end_iter())
        self.write (self.prompt, 'prompt')
        self.write (line)


    def write (self, line, style=None):
        """ Write a line using given style (if any) """
    
        start,end = self.text.get_buffer().get_bounds()

        if style==None:
            self.text.get_buffer().insert (end, line)
        else:
            self.text.get_buffer().insert_with_tags_by_name (end, line, style)
        self.text.scroll_mark_onscreen (self.buffer.get_insert())
        self.linestart = self.buffer.get_end_iter().get_offset()

    def replace (self, line):
        """ Replace current active line with line """
    
        start,end = self.current_line_bounds()
        self.text.get_buffer().delete (start,end)
        l = self.linestart
        self.write (line)
        self.linestart = l


    def current_line (self):
        """ Get current active line """
        
        start, end = self.current_line_bounds()
        return self.buffer.get_text (start,end,True)


    def current_line_bounds (self):
        """ Get current active line bounds """
        
        l = self.buffer.get_line_count() - 1
        start = self.buffer.get_iter_at_line(l)
        #mark = self.buffer.get_mark('linestart')
        #start = self.buffer.get_iter_at_mark (mark)

        tag = self.buffer.get_tag_table().lookup('prompt')

        while not start.ends_tag(tag):
            start.forward_char()
        
        #if start.get_chars_in_line() >= PSLEN:
        #    start.forward_chars(PSLEN)
        
        end = self.buffer.get_end_iter()
        return start,end


    def is_balanced (self, line):
        """ Checks line balance for brace, bracket, parenthese and string quote

        This helper function checks for the balance of brace, bracket,
        parenthese and string quote. Any unbalanced line means to wait until
        some other lines are fed to the console.
        """
        
        s = line
        s = filter(lambda x: x in '()[]{}"\'', s)
        s = s.replace ("'''", "'")
        s = s.replace ('"""', '"')
        instring = False
        brackets = {'(':')', '[':']', '{':'}', '"':'"', '\'':'\''}
        stack = []
        
        while len(s):
            if not instring:
                if s[0] in ')]}':
                    if stack and brackets[stack[-1]] == s[0]:
                        del stack[-1]
                    else:
                        return False
                elif s[0] in '"\'':
                    if stack and brackets[stack[-1]] == s[0]:
                        del stack[-1]
                        instring = False
                    else:
                        stack.append(s[0])
                        instring = True
                else:
                    stack.append(s[0])
            else:
                if s[0] in '"\'' and stack and brackets[stack[-1]] == s[0]:
                    del stack[-1]
                    instring = False
            s = s[1:]
        return len(stack) == 0


    def eval (self):
        """ Evaluate if current line is ready for execution """
        
        l = self.current_line()
        self.write ('\n', 'normal')
        self.history.append (l)
        end = self.buffer.get_end_iter()
        self.buffer.place_cursor(end)

        if l == '':
            cmd = self.cmd
            self.cmd = ''
            self.execute (cmd)
            self.prompt1()
            return

        self.cmd = self.cmd + l + '\n'
        if not self.is_balanced (self.cmd):
            self.prompt2()
            return
        l = l.rstrip()
        if len(l) > 0:
            if l[-1] == ':' or l[-1] == '\\' or l[0] in ' \11':
                self.prompt2()
                return

        cmd = self.cmd
        self.cmd = ''
        self.execute (cmd)
        self.prompt1()
        return


    def idle (self, frame, event, arg):
        """ Idle function to be used when running a command.
        
        This idle function is set as a trace function when executing some
        commands, it allows to process gtk events even when executing code.
        """
        
        while gtk.events_pending():
            gtk.main_iteration()
        return self.idle


    def execute (self, cmd):
        """ Execute a given command """

        if self.emit('eval', cmd):
            return

        sys.stdout, self.stdout = self.stdout, sys.stdout
        sys.stderr, self.stderr = self.stderr, sys.stderr
        sys.stdin,  self.stdin  = self.stdin,  sys.stdin
        try:
            try:
                r = eval (cmd, self.namespace, self.namespace)
                self.namespace["_"] = r
                if r is not None:
                    print `r`
            except SyntaxError:
                exec cmd in self.namespace
        except:
            if hasattr (sys, 'last_type') and sys.last_type == SystemExit:
                self.quit_handler()
            else:
                try:
                    tb = sys.exc_traceback
                    if tb:
                        tb=tb.tb_next
                    traceback.print_exception (sys.exc_type, sys.exc_value, tb)
                except:
                    sys.stderr, self.stderr = self.stderr, sys.stderr
                    traceback.print_exc()
        sys.stdout, self.stdout = self.stdout, sys.stdout
        sys.stderr, self.stderr = self.stderr, sys.stderr
        sys.stdin,  self.stdin  = self.stdin,  sys.stdin


    def open (self, filename):
        """ Open and execute a given filename """
        
        if not filename:
            return
        if not os.path.exists (filename):
            dialog = gtk.MessageDialog(
                   None, gtk.DIALOG_DESTROY_WITH_PARENT,
                   gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                   "Unable to open '%s', the file does not exist." % filename)
            dialog.run()
            dialog.destroy()
            return
        
        f = open(filename)
        try:
            self.write ("Executing '%s'\n\n" % filename, 'extern')
            for line in f:
                self.write ('\t'+line, 'script')
            self.write ('\n', 'normal')
            self.execute ("execfile('%s')" % filename)
            self.prompt1()
        finally:
            f.close()

    def quit (self, *args):
        """ Default handler on quit """
        gtk.main_quit();
        return True

    def on_drag_data_received (self, 
                               widget, context, x, y, selection, info, etime):
        """ Handler for drag data """
        
        self.write (selection.data)
        widget.emit_stop_by_name ("drag-data-received")
        self.text.grab_focus()


    def on_key_pressed (self, widget, event):
        """ Key pressed handler """

        tab_pressed = self.tab_pressed
        self.tab_pressed = 0

        # Enter
        if event.keyval == gtk.keysyms.Return or \
           event.keyval == gtk.keysyms.KP_Enter:

            if self.input_mode:
                self.input_mode = False
                end = self.buffer.get_end_iter()
                start = self.buffer.get_iter_at_offset (self.linestart)
                self.input = self.buffer.get_text (start,end,True)

                self.buffer.remove_all_tags(start, end)
                self.buffer.apply_tag_by_name('script', start, end)

                self.write('\n', 'normal')
            else:
                start, end = self.current_line_bounds()
                self.buffer.remove_all_tags(start, end)
                self.buffer.apply_tag_by_name('script', start, end)

                self.eval()

            return True
        
        # Previous command
        elif event.keyval in (gtk.keysyms.KP_Up, gtk.keysyms.Up):
            if not self.input_mode:
                self.replace (self.history.prev (self.current_line())) 
            return True
        
        # Next command
        elif event.keyval in (gtk.keysyms.KP_Down, gtk.keysyms.Down):
            if not self.input_mode:
                self.replace (self.history.next (self.current_line()))
            return True
        
        # Left arrow (control cursor position relative to prompt)
        elif event.keyval in (gtk.keysyms.KP_Left, gtk.keysyms.Left):
            iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            if iter.get_offset() == self.linestart:
                return True
            return False
        
        # Backspace
        elif event.keyval == gtk.keysyms.BackSpace:
            iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            if iter.get_offset() == self.linestart:
                return True
            return False

        # Home
        elif event.keyval == gtk.keysyms.Home:
            start = self.buffer.get_iter_at_offset (self.linestart)
            self.text.get_buffer().place_cursor(start)
            return True

        # Tab completion
        elif event.keyval == gtk.keysyms.Tab:
            if not self.input_mode:
                end = self.buffer.get_end_iter()
                start = self.buffer.get_iter_at_offset(self.linestart)
                txt = self.buffer.get_text(start, end, True)
                
                self.tab_pressed += tab_pressed + 1
                self.complete(txt)

                return True

        elif event.state & gtk.gdk.CONTROL_MASK:
            # Ctrl-A
            if event.keyval in (gtk.keysyms.A, gtk.keysyms.a):
                start = self.buffer.get_iter_at_offset (self.linestart)
                self.text.get_buffer().place_cursor(start)
                return True

            # Ctrl-E
            elif event.keyval in (gtk.keysyms.E, gtk.keysyms.e):
                if self.input_mode:
                   return True
                end = self.buffer.get_end_iter()
                self.buffer.place_cursor (end)
                return True

            # Ctrl-D
            elif event.keyval in (gtk.keysyms.D, gtk.keysyms.d):
                if self.input_mode:
                    return True     
                iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
                if iter.get_line_offset() == PSLEN:
                    self.quit_handler()
                return True
            
            # Ctrl-L
            elif event.keyval in (gtk.keysyms.L, gtk.keysyms.l):
                if not self.input_mode:
                    self.clear()
                return True
        return False

gobject.type_register(Console)

# =============================================================================
class ConsoleWindow:
    """ Interactive GTK console window """

    def __init__ (self, ns, title='Python', command=None):
        """ Initialize s console window """
        
        self.win = gtk.Window()
        self.win.set_default_size (640, 400)
        self.win.set_border_width (3)
        self.win.connect ("destroy", lambda w: gtk.main_quit())
        self.win.connect ("delete_event", lambda w,e: gtk.main_quit())
        self.win.set_title (title)
        self.console = Console (namespace=ns)
        self.win.add (self.console)
        self.console.banner ()
        if command:
            self.console.execute (command)
        self.win.show_all()
        
        logo = ["16 16 4 1",
                " 	c None", ".	c #476F90", "+	c #FFE35E", "@	c #F3F6F3",
                "     @@@@@      ",
                "    @@...@@     ",
                "    @.@...@     ",
                "    @.....@     ",
                " @@@@@@...@@@@  ",
                "@@........@++@@ ",
                "@.........@+++@ ",
                "@....@@@@@++++@ ",
                "@...@+++++++++@ ",
                "@@..@++++++++@@ ",
                " @@@@+++@@@@@@  ",
                "    @+++++@     ",
                "    @+++@+@     ",
                "    @@++++@     ",
                "     @@@@@      ",
                "                "]
 
        pixbuf = gtk.gdk.pixbuf_new_from_xpm_data(logo)
        self.win.set_icon (pixbuf)
        return


if __name__ == '__main__':
    conswin = ConsoleWindow ({'__builtins__': __builtins__,
                              '__name__': '__main__',
                              '__doc__': None},
                              title = 'Python Console')
    if len(sys.argv) > 1:
        conswin.console.open (sys.argv[1])
    gtk.main()

