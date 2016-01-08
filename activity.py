# -*- coding: utf-8 -*-
import os

from gettext import gettext as _
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
import pygame
import sugar3.activity.activity
import libraries
libraries.setup_path()
import sugargame2
import sugargame2.canvas
import spyral

import logging
import traceback
import helpbutton

from sugar3.graphics import style
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.radiotoolbutton import RadioToolButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.alert import NotifyAlert

from libraries.console.interactiveconsole import GTKInterpreterConsole
from libraries.pyvimwrapper.vimWrapper import VimWrapper
from gi.repository import GtkSource

from pango import FontDescription

import game.neko
import game.credits

JUEGO=game.neko

def is_xo():
    return os.path.exists('/sys/power/olpc-pm')

class Activity(sugar3.activity.activity.Activity):
    def __init__(self, handle):
        super(Activity, self).__init__(handle)
        self.paused = False

        watch = Gdk.Cursor.new(Gdk.CursorType.WATCH)
        self.get_window().set_cursor(watch)

        self.p = Gtk.VPaned()
        self.p.connect("notify::position", self.redraw)
        self.box = Gtk.Notebook()
        self.p.pack2(self.box)
        self.p.show()
        self.box.set_show_tabs(False)

        self.splash = Gtk.Image()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file("images/splash_neko.png")
        screen = self.window.get_screen()
        width, height = screen.get_width(), screen.get_height() - style.GRID_CELL_SIZE
        pixbuf = pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)
        self.splash.set_from_pixbuf(pixbuf)
        self.splash.show()
        eb = Gtk.EventBox()
        eb.add(self.splash)
        eb.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("white"))
        eb.show()
        self.box.append_page(eb, Gtk.Label(label="Inicio"))

        self._pygamecanvas = sugargame2.canvas.PygameCanvas(self)
        self._pygamecanvas.set_flags(Gtk.AttachOptions.EXPAND)
        self._pygamecanvas.set_flags(Gtk.AttachOptions.FILL)

        self.connect("visibility-notify-event", self.redraw)
        self._pygamecanvas.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self._pygamecanvas.connect("button-press-event", self._pygamecanvas.grab_focus)
        self.box.append_page(self._pygamecanvas, Gtk.Label(label="Juego"))

        self.box.show()
        self.set_canvas(self.p)

        GObject.timeout_add(300, self.pump)
        GObject.timeout_add(2000, self.init_interpreter)
        #GObject.timeout_add(1000, self.build_editor)
        GObject.timeout_add(1500, self.check_modified)

        self.build_toolbar()
        self.credits = None
        self.editor = None
        #self.reader = None
        self._pygamecanvas.run_pygame(self.run_game)

    def redraw(self, widget=None, b=None, c=None):
        scene = spyral.director.get_scene()
        if scene:
            scene.redraw()

    def alert(self, title=None, text=None, delay=5):
        alert = NotifyAlert(delay)
        alert.props.title = title
        alert.props.msg = text
        self.add_alert(alert)
        alert.connect('response', self._alert_ok)
        alert.show()

    def _alert_ok(self, alert, *args):
        self.remove_alert(alert)

    def check_modified(self):
        if self.box.current_page()==2:
            if not self.save_button.get_sensitive():
                if self.editor.modificado():
                    self.save_button.set_sensitive(True)
                    return False
        return True

    def pump(self):
        # Esto es necesario porque sino pygame acumula demasiados eventos.
        pygame.event.pump()

    def focus_interpreter(self, widget, event):
        self._interpreter.text.grab_focus()
        return True

    def init_interpreter(self):
        # diferido unos segundos para evitar ver errores superfluos al iniciar
        self._interpreter = GTKInterpreterConsole(self.redraw)
        self._interpreter.text.connect('button-press-event', self.focus_interpreter)
        self.p.pack1(self._interpreter)
        return False

    def open_file(self, widget, path):
        if path:
            if not os.path.isdir(path):
                self.editor.open_file(widget, path)

    def save_file(self, widget):
        if self.editor.modificado():
            self.save_button.set_sensitive(False)
            self.editor.save_file()
            filename = self.editor.current_file()
            self.alert(filename, "Archivo guardado.")
            GObject.timeout_add(1500, self.check_modified)

    def build_editor(self):
        dir_real = os.getcwd()
        f = os.path.realpath(JUEGO.__file__)
        f = "." + f.replace(dir_real ,"") # todo esto para obtener una ruta relativa
        f = f.rstrip("c")  # en caso que sea .pyc compilado

        self.h = Gtk.HPaned()
        self.tree = FileViewer(".", os.path.basename(f))
        self.tree.connect("file-selected", self.open_file)
        self.tree.show()
        self.h.pack1(self.tree)
        self.box.append_page(self.h, Gtk.Label(label="Editor"))

        if False:
            self.socket = Gtk.Socket()
            self.socket.show()
            self.h.pack2(self.socket)
            sock_id = str(self.socket.get_id())
            self.editor = VimSourceView(sock_id)

            if not self.editor.bufInfo.bufferList:
                f = JUEGO.__file__
                if f.endswith("pyc"):
                    f = f[:-1]
                self.open_file(None, f)
        else:
            self.editor = SourceView()

            scroller = Gtk.ScrolledWindow()
            scroller.set_policy(Gtk.PolicyType.AUTOMATIC,
                          Gtk.PolicyType.AUTOMATIC)
            scroller.add(self.editor)
            scroller.show()
            self.h.pack2(scroller)
            self.editor.show()

        self.h.show()
        self.open_file(None, f)

    def build_reader(self):
        self.reader = webkit.WebView()
        curdir = os.getcwd()
        self.reader.load_uri("file://%s/docs/index.html" % curdir)
        self.box.append_page(self.reader, Gtk.Label(label="Lector"))
        self.reader.show()

    def build_toolbar(self):
        toolbar_box = ToolbarBox()
        self.set_toolbar_box(toolbar_box)
        toolbar_box.show()

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, -1)
        activity_button.show()

        tool_group = None

        self.game_button = RadioToolButton()
        self.game_button.props.icon_name = 'gamecanvas'
        self.game_button.set_tooltip(_('Juego'))
        self.game_button.accelerator = "<Ctrl>1"
        self.game_button.props.group = tool_group
        self.game_button.connect('clicked', self.show_game)
        toolbar_box.toolbar.insert(self.game_button, -1)
        self.game_button.show()
        tool_group = self.game_button

        button = RadioToolButton()
        button.props.icon_name = 'view-source'
        button.set_tooltip(_('Editor'))
        button.accelerator = "<Ctrl>2"
        button.props.group = tool_group
        button.connect('clicked', self.show_editor)
        toolbar_box.toolbar.insert(button, -1)
        button.show()

        self.save_button = ToolButton('dialog-ok')
        self.save_button.set_tooltip(_('Guardar'))
        self.save_button.accelerator = "<Ctrl>s"
        self.save_button.connect('clicked', self.save_file)
        self.save_button.set_sensitive(False)
        toolbar_box.toolbar.insert(self.save_button, -1)
        self.save_button.show()

        separator = Gtk.SeparatorToolItem()
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        button = ToolButton('system-restart')
        button.set_tooltip(_('Reiniciar juego'))
        button.accelerator = "<Alt><Shift>r"
        button.connect('clicked', self.restart_game)
        toolbar_box.toolbar.insert(button, -1)
        button.show()

        self.editor_button = ToolButton('sources')
        self.editor_button.set_tooltip(_('Consola'))
        self.editor_button.accelerator = "<Ctrl>grave"
        self.editor_button.connect('clicked', self.toggle_console)
        toolbar_box.toolbar.insert(self.editor_button, -1)
        self.editor_button.show()

        separator = Gtk.SeparatorToolItem()
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        button = helpbutton.HelpButton(self)
        toolbar_box.toolbar.insert(button, -1)
        button.show()

        button = ToolButton()
        button.props.icon_name = 'activity-about'
        button.set_tooltip(_('Acerca de'))
        button.accelerator = "<Ctrl>i"
        button.connect('clicked', self.run_credits)
        toolbar_box.toolbar.insert(button, -1)
        button.show()

        # Blank space (separator) and Stop button at the end:
        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

    def run_game(self):
        spyral.director.init((0,0), fullscreen=False, max_fps=30)
        self.game = JUEGO.Juego(self, callback=self.game_ready)
        self.box.connect("switch-page", self.redraw)
        spyral.director.push(self.game)
        self.start()

    def run_credits(self, widget):
        if not (spyral.director.get_scene()==self.credits):
            self.credits = game.credits.Creditos(self.game.size)
            spyral.director.push(self.credits)

    def start(self):
        try:
            spyral.director.run(sugar = True)
        except AttributeError as detail:
            detail2 = traceback.format_exc()
            self.box.set_page(0)
            self.alert( detail2, "Spyral se ha detenido abruptamente.", 60)

    def show_game(self, widget):
        self.box.set_page(1)
        self.redraw()

    def show_editor(self, widget):
        if not self.editor:
            self.build_editor()
        self.box.set_page(2)
        self.redraw()

    def show_reader(self, widget):
        if not self.reader:
            self.build_reader()
        self.box.set_page(3)
        self.redraw()

    def restart_game(self, widget):
        global JUEGO
        import objetos
        try:
            objetos.reset()
        except AttributeError:
            pass
        self.box.set_page(0)
        watch = Gdk.Cursor.new(Gdk.CursorType.WATCH)
        self.window.set_cursor(watch)
        JUEGO = reload(JUEGO)
        self.game = JUEGO.Juego(self, callback=self.game_ready)
        spyral.director.replace(self.game)
        self.start()

    def game_ready(self, widget = None):
        self.game_button.set_active(True)
        self.box.set_page(1)
        self._pygamecanvas.grab_focus()
        self.window.set_cursor(None)

    def read_file(self, file_path):
        pass

    def write_file(self, file_path):
        pass

    def can_close(self):
        if self.editor:
            self.editor.close()
        self.box.set_page(0)
        try:
            spyral.director.quit()
        except spyral.exceptions.GameEndException:
            pass
        finally:
            return True

    def toggle_console(self, e):
        if self._interpreter.props.visible:
            self._interpreter.hide()
            self._pygamecanvas.grab_focus()
        else:
            self.p.set_position(160)
            self._interpreter.show()
            self._interpreter.text.grab_focus()
        self.redraw()

    def animate_console(self):
        easing = spyral.easing.Linear(0,160)
        self.p.set_position(0)


_EXCLUDE_EXTENSIONS = ('.pyc', '.pyo', '.so', '.o', '.a', '.la', '.mo', '~',
                       '.xo', '.tar', '.bz2', '.zip', '.gz', '.swp')
_EXCLUDE_NAMES = ['.deps', '.libs', '.git']

class FileViewer(Gtk.ScrolledWindow):
    __gtype_name__ = 'SugarFileViewer'

    __gsignals__ = {
        'file-selected': (GObject.SignalFlags.RUN_FIRST,
                           None,
                           ([str])),
    }

    def __init__(self, path, initial_filename):
        GObject.GObject.__init__(self)

        self.props.hscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        self.props.vscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        self.set_size_request(style.GRID_CELL_SIZE * 3, -1)

        self._path = None
        self._initial_filename = initial_filename

        self._tree_view = Gtk.TreeView()
        self.add(self._tree_view)
        self._tree_view.show()

        self._tree_view.props.headers_visible = False
        selection = self._tree_view.get_selection()
        selection.connect('changed', self.__selection_changed_cb)

        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn()
        column.pack_start(cell, True)
        column.add_attribute(cell, 'text', 0)
        self._tree_view.append_column(column)
        self._tree_view.set_search_column(0)

        self.set_path(path)

    def set_path(self, path):
        self.emit('file-selected', None)
        if self._path == path:
            return

        self._path = path
        self._tree_view.set_model(Gtk.TreeStore(str, str))
        self._model = self._tree_view.get_model()
        self._add_dir_to_model(path)

    def _add_dir_to_model(self, dir_path, parent=None):
        dir_list = sorted(os.listdir(dir_path))
        #file_list = sorted([f for f in os.listdir(dir_path) if os.path.isfile(f)])
        for f in dir_list:
            if f.endswith(_EXCLUDE_EXTENSIONS) or f in _EXCLUDE_NAMES:
                continue

            full_path = os.path.join(dir_path, f)
            if os.path.isdir(full_path):
                new_iter = self._model.append(parent, [f, full_path])
                self._add_dir_to_model(full_path, new_iter)
            else:
                current_iter = self._model.append(parent, [f, full_path])
                if f == self._initial_filename:
                    if parent:
                        treepath = self._model.get_path(current_iter)
                        self._tree_view.expand_to_path(treepath)
                    selection = self._tree_view.get_selection()
                    selection.select_iter(current_iter)
                    self.thisisit = current_iter

    def __selection_changed_cb(self, selection):
        model, tree_iter = selection.get_selected()
        if tree_iter is None:
            file_path = None
        else:
            file_path = model.get_value(tree_iter, 1)
        self.emit('file-selected', file_path)

class VimSourceView(VimWrapper):
    """
    Visor de código basado en GVim
    TENÍA QUE HACERLO :-)
    """

    def __init__(self, sock_id):
        VimWrapper.__init__(self,  vimExec = "/usr/bin/gvim")

        self.start(sock_id=sock_id)
        self.sendKeys(":set guioptions=M<CR>i")
        self.bufInfo.addEventHandler(self.event_handler)

    def open_file(self, widget, path):
        if path:
            if not os.path.isdir(path):
                self.sendKeys(":e %s<CR>" % path)
                if is_xo:
                    self.fix_fonts()

    def fix_fonts(self):
        font = "Monospace\\ " + str(int(10/style.ZOOM_FACTOR))
        self.sendKeys(":set guifont=%s<CR>" % font)

    def save_file(self):
        self.sendKeys(":w<CR>")

    def event_handler(self, event, path):
        logging.debug("EVENT, %s, %s" % (event, path))
        if event=="killed":
            self.close()

    def modificado(self):
        return self.isBufferModified(-1)

    def current_file(self):
        cur_buf = self.getBufId()
        filename = self.bufInfo.pathOfBufId(cur_buf)
        return filename

class SourceView(GtkSource.View):
    """
    Visor de código para archivos abiertos.
    """

    def __init__(self):
        GtkSource.View.__init__(self)

        self.archivo = False

        self.set_show_line_numbers(True)

        self.set_insert_spaces_instead_of_tabs(True)
        self.set_tab_width(4)
        self.set_auto_indent(True)

        font = "Monospace " + str(int(10/style.ZOOM_FACTOR))
        self.modify_font(FontDescription(font))

        self.show_all()

    def close(self):
        pass

    def init_syntax(self):
        text_buffer = self.get_buffer()
        lang_manager = GtkSource.LanguageManager.get_default()
        if hasattr(lang_manager, 'list_languages'):
            langs = lang_manager.list_languages()
        else:
            lang_ids = lang_manager.get_language_ids()
            langs = [lang_manager.get_language(lang_id)
                     for lang_id in lang_ids]
        for lang in langs:
            for m in lang.get_mime_types():
                if m == "text/x-python":
                    text_buffer.set_language(lang)

        if hasattr(text_buffer, 'set_highlight'):
            text_buffer.set_highlight(True)
        else:
            text_buffer.set_highlight_syntax(True)

        mgr = GtkSource.StyleSchemeManager.get_default()
        style_scheme = mgr.get_scheme('oblivion')
        self.get_buffer().set_style_scheme(style_scheme)

    def open_file(self, widget, archivo):
        """
        Setea el archivo cuyo codigo debe mostrarse.
        """

        if archivo:
            if os.path.isfile(archivo):
                self.archivo = archivo
                texto_file = open(self.archivo, 'r')
                texto = texto_file.read()
                texto_file.close()

                self.set_buffer(GtkSource.Buffer())
                self.get_buffer().begin_not_undoable_action()
                #self.__set_lenguaje(self.archivo)
                self.get_buffer().set_text(texto)

                nombre = os.path.basename(self.archivo)
                self.control = os.path.getmtime(self.archivo)
        else:
            self.set_buffer(GtkSource.Buffer())
            self.get_buffer().begin_not_undoable_action()

        self.get_buffer().end_not_undoable_action()
        self.get_buffer().set_modified(False)

        pos = self.get_iter_at_location(1,1)
        self.get_buffer().place_cursor(pos)
        self.scroll_to_iter(pos, False)

        self.grab_focus()
        self.init_syntax()

    def save_file(self):
        if self.archivo:
            buffer = self.get_buffer()

            if buffer.get_modified() and os.path.exists(self.archivo):

                inicio, fin = buffer.get_bounds()
                texto = buffer.get_text(inicio, fin, 0)

                archivo = open(self.archivo, "w")
                archivo.write(texto)
                archivo.close()

                buffer.set_modified(False)
                self.control = os.path.getmtime(self.archivo)

    def modificado(self):
        return self.get_buffer().get_modified()

    def current_file(self):
        return os.path.realpath(self.archivo)

def main():
    spyral.director.init((0,0), fullscreen = False, max_fps = 30)
    import game
    game.main()
    try:
        spyral.director.run()
    except KeyboardInterrupt:
        spyral.director.quit()

if __name__ == '__main__':
    main()
