#!/usr/bin/env python

import gtk, gobject, sqlite3
from os.path import basename
import os

base_title = "LearnHelper editor"

class DBEditor():

    def __init__(self):
        self.window = gtk.Window()
        self.window.connect("delete_event", self.exit, False)
        self.window.connect("destroy", gtk.main_quit)
        self.window.set_title(base_title)
        self.window.set_default_size(500, 300)
        self.main_vbox = gtk.VBox()

        self.menu_bar = gtk.MenuBar()
        self.file_menu = gtk.Menu()
        self.open_item = gtk.MenuItem("Open")
        self.save_item = gtk.MenuItem("Save")
        self.exit_item = gtk.MenuItem("Exit")
        self.langs_menu_item = gtk.MenuItem("Languages")
        self.file_menu.append(self.open_item)
        self.file_menu.append(self.save_item)
        self.file_menu.append(gtk.SeparatorMenuItem())
        self.file_menu.append(self.langs_menu_item)
        self.file_menu.append(gtk.SeparatorMenuItem())
        self.file_menu.append(self.exit_item)
        self.file_menu_item = gtk.MenuItem("File")
        self.file_menu_item.set_submenu(self.file_menu)
        self.menu_bar.append(self.file_menu_item)
        self.open_item.connect("activate", self.open_db)
        self.save_item.connect("activate", self.save_db)
        self.exit_item.connect("activate", self.exit)
        self.langs_menu_item.connect("activate", self.languages_menu)

        self.hb_words = gtk.HBox()
        self.scr_words = gtk.ScrolledWindow()
        self.scr_words.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.words = gtk.TreeView()
        self.words.connect("cursor-changed", self.word_selected)
        self.scr_words.add(self.words)
        self.hb_words.pack_start(self.scr_words)
        self.words_controls = gtk.VBox()
        self.add_word = gtk.Button()
        self.add_word.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON))
        self.add_word.connect("clicked", self.do_add_word)
        self.remove_word = gtk.Button()
        self.remove_word.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON))
        self.remove_word.connect("clicked", self.do_remove_word)
        self.words_controls.pack_start(self.add_word, True, False)
        self.words_controls.pack_start(self.remove_word, True, False)
        self.hb_words.pack_start(self.words_controls, False)

        self.hb_translations = gtk.HBox()
        self.scr_translations = gtk.ScrolledWindow()
        self.scr_translations.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.translations = gtk.TreeView()
        self.scr_translations.add(self.translations)
        self.hb_translations.pack_start(self.scr_translations)
        self.translations_controls = gtk.VBox()
        self.add_translation = gtk.Button()
        self.add_translation.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON))
        self.add_translation.connect("clicked", self.do_add_translation)
        self.remove_translation = gtk.Button()
        self.remove_translation.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON))
        self.remove_translation.connect("clicked", self.do_remove_translation)
        self.translations_controls.pack_start(self.add_translation, True, False)
        self.translations_controls.pack_start(self.remove_translation, True, False)
        self.hb_translations.pack_start(self.translations_controls, False)

        self.main_vbox.pack_start(self.menu_bar, False)
        self.main_vbox.pack_start(self.hb_words)
        self.main_vbox.pack_start(self.hb_translations)

        self.words_store = gtk.ListStore(str, str, gobject.TYPE_PYOBJECT, int)
        self.words.set_model(self.words_store)
        self.combo_renderer = gtk.CellRendererCombo()
        self.combo_renderer.set_property("has-entry", False)
        self.combo_renderer.set_property("editable", True)
        self.combo_renderer.set_property("text-column", 0)
        self.combo_renderer.connect("edited", self.lingua_changed, self.words_store)
        self.words.append_column(gtk.TreeViewColumn("Language", self.combo_renderer, text=0))
        text_render = gtk.CellRendererText()
        text_render.set_property("editable", True)
        text_render.connect("edited", self.word_edited, self.words_store)
        self.words.append_column(gtk.TreeViewColumn("Word", text_render, text=1))

        self.translations_store = gtk.ListStore(str)
        self.translations.set_model(self.translations_store)
        text_render = gtk.CellRendererText()
        text_render.set_property("editable", True)
        text_render.connect("edited", self.translation_edited)
        self.translations.append_column(gtk.TreeViewColumn("Translation", text_render, text=0))

        self.window.add(self.main_vbox)
        self.window.show_all()

        self.db = None
        self.cursor = None

        self.modified = False
        self.open_db(None)

    def open_db(self, item):
        dialog = gtk.FileChooserDialog(
            "Select database file",
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                     gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        filter = gtk.FileFilter()
        filter.set_name("SQLite databases")
        filter.add_pattern("*.db")
        filter.add_mime_type("application/x-sqlite3")
        dialog.add_filter(filter)
        dialog.set_current_folder(".")
        dialog.run()
        dialog.hide()

        filename = dialog.get_filename()
        if not filename:
            return
        if self.cursor:
            self.cursor.close()
            self.db.commit()
        self.db = sqlite3.connect(filename)
        self.cursor = self.db.cursor()

        self.linguas = dict(self.cursor.execute("SELECT id, lang FROM dictionaries"))
        linguas_model = gtk.ListStore(str)
        for key in sorted(self.linguas):
            linguas_model.append((self.linguas[key],))
        self.combo_renderer.set_property("model", linguas_model)
        words = self.cursor.execute("SELECT lang_id, word, translation, id FROM words")
        for lang, word, translation, id in words:
            translations = gtk.ListStore(str)
            if translation:
                for tr in translation.split("|"):
                    translations.append((tr,))
            self.words_store.append((self.linguas[lang], word, translations, id))

        self.linguas_model = linguas_model
        self.window.set_title("%s - %s" % (basename(filename), base_title))

    def lingua_changed(self, widget, path, text, model):
        model[path][0] = text
        self.modified = True
        r_lang = None
        for lang_id, lang in self.linguas.items():
            if lang == text:
                r_lang = lang_id
        if r_lang is not None:
            self.cursor.execute("UPDATE words SET lang_id = ? WHERE word = ?", (r_lang, unicode(model[path][1])))

    def word_selected(self, widget):
        it = self.words_store.get_iter(widget.get_cursor()[0])
        self.translations.set_model(self.words_store.get(it, 2)[0])

    def word_edited(self, widget, path, text, model):
        self.modified = True
        model[path][1] = text
        self.cursor.execute("UPDATE words SET word = ? WHERE id = ?", (unicode(text), model[path][3]))

    def translation_edited(self, widget, path, text):
        model = self.words_store.get(self.words_store.get_iter(self.words.get_cursor()[0]), 2)[0]
        model[path][0] = text
        self.update_translations()

    def do_add_word(self, widget):
        self.modified = True
        res = self.cursor.execute("INSERT INTO words (lang_id, last_repeat) VALUES (1, 0)")
        tr_model = gtk.ListStore(str)
        self.words_store.append((self.linguas[1], "", tr_model, res.lastrowid))
        self.words.set_cursor(self.words_store.iter_n_children(None) - 1,
                              self.words.get_column(1),
                              True)
        self.do_add_translation(None, False)

    def do_remove_word(self, widget):
        try:
            it = self.words_store.get_iter(self.words.get_cursor()[0])
            id = self.words_store.get(it, 3)[0]
            self.cursor.execute("DELETE FROM words WHERE id = ?", (id, ))
            self.words_store.remove(it)
            self.modified = True
            self.translations.set_model(self.translations_store)
        except TypeError:
            pass

    def do_add_translation(self, widget, scroll=True):
        if self.words.get_cursor()[0] is None:
            return
        model = self.translations.get_model()
        model.append(("New translation",))
        if scroll:
            self.translations.set_cursor(model.iter_n_children(None) - 1,
                                         self.translations.get_column(0),
                                         True)

    def do_remove_translation(self, widget):
        if self.translations.get_cursor()[0] is None or self.words.get_cursor()[0] is None:
            return
        model = self.translations.get_model()
        it = model.get_iter(self.translations.get_cursor()[0])
        model.remove(it)
        self.update_translations()

    def update_translations(self):
        self.modified = True
        linguas = dict((lang, id) for id, lang in self.linguas.items())
        it = self.words_store.get_iter(self.words.get_cursor()[0])
        id = self.words_store.get(it, 3)[0]
        trans = self.words_store.get(it, 2)[0]
        self.cursor.execute("UPDATE words SET translation = ? WHERE id = ?", ("|".join(map(lambda x: unicode(x[0]), list(trans))), id))

    def save_db(self, widget):
        self.modified = False
        self.db.commit()

    def languages_menu(self, widget):
        def do_add_lingua(widget):
            self.modified = True
            self.linguas_model.append(("New language",))
            res = self.cursor.execute("INSERT INTO dictionaries (lang, repeat_time) VALUES (\"New language\", 259200)")
            self.linguas[res.lastrowid] = "New language"

        def do_remove_lingua(widget, tree_view):
            path = tree_view.get_cursor()[0]
            if path is None:
                return
            self.modified = True
            it = self.linguas_model.get_iter(path)
            lingua = self.linguas_model.get(it, 0)[0]
            res = self.cursor.execute("DELETE FROM dictionaries WHERE lang = ?", (unicode(lingua),))
            for key, item in self.linguas.items():
                if item == lingua:
                    del self.linguas[key]
                    self.cursor.execute("UPDATE words SET lang_id = 1 WHERE lang_id = ?", (key,))
                    break
            self.linguas_model.remove(it)

        def do_edit_lingua(widget, path, text):
            self.modified = True
            prev_text = self.linguas_model[path][0]
            for key, item in self.linguas.items():
                if item == prev_text:
                    self.linguas[key] = text
                    lang_id = key
                    break
            self.linguas_model[path][0] = text
            self.cursor.execute("UPDATE dictionaries SET lang = ? WHERE lang = ?", (unicode(text), unicode(prev_text)))

        dialog = gtk.Dialog("Languages",
                            self.window,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        hbox = gtk.HBox()
        button_vbox = gtk.VBox()
        add_lingua = gtk.Button()
        add_lingua.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON))
        remove_lingua = gtk.Button()
        remove_lingua.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON))
        button_vbox.pack_start(add_lingua, True, False)
        button_vbox.pack_start(remove_lingua, True, False)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        tree_view = gtk.TreeView(self.linguas_model)
        cell_renderer = gtk.CellRendererText()
        cell_renderer.set_property("editable", True)
        tree_view.append_column(gtk.TreeViewColumn("Language", cell_renderer, text=0))
        scrolled_window.add(tree_view)
        hbox.pack_start(scrolled_window)
        hbox.pack_start(button_vbox, False, False)
        hbox.show_all()

        dialog.vbox.pack_start(hbox)

        add_lingua.connect("clicked", do_add_lingua)
        remove_lingua.connect("clicked", do_remove_lingua, tree_view)
        cell_renderer.connect("edited", do_edit_lingua)
        dialog.run()
        dialog.destroy()

    def exit(self, widget, event=None, do_exit=True):
        if self.modified:
            md = gtk.MessageDialog(self.window,
                                   gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_YES_NO, "Are you sure? You have unsaved changes!")
            result = md.run()
            md.destroy()
        if not self.modified or result == gtk.RESPONSE_YES:
            if do_exit:
                self.window.destroy()
            return False
        else:
            return True

if __name__ == '__main__':
    editor = DBEditor()
    gtk.main()
