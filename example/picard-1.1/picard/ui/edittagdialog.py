# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2011 Michael Wiencek
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from PyQt4 import QtCore, QtGui
from picard.util.tags import TAG_NAMES
from picard.ui.ui_edittagdialog import Ui_EditTagDialog


class EditTagDialog(QtGui.QDialog):

    def __init__(self, window, tag):
        QtGui.QDialog.__init__(self, window)
        self.ui = Ui_EditTagDialog()
        self.ui.setupUi(self)
        self.window = window
        self.value_list = self.ui.value_list
        self.metadata_box = window.metadata_box
        self.tag = tag
        self.modified_tags = {}
        self.different = False
        self.default_tags = sorted(set(TAG_NAMES.keys() + self.metadata_box.tag_names))
        tag_names = self.ui.tag_names
        tag_names.editTextChanged.connect(self.tag_changed)
        tag_names.addItem("")
        tag_names.addItems([tn for tn in self.default_tags if not tn.startswith("~")])
        self.tag_changed(tag)
        self.value_selection_changed()
        self.ui.edit_value.clicked.connect(self.edit_value)
        self.ui.add_value.clicked.connect(self.add_value)
        self.ui.remove_value.clicked.connect(self.remove_value)
        self.value_list.itemChanged.connect(self.value_edited)
        self.value_list.itemSelectionChanged.connect(self.value_selection_changed)

    def edit_value(self):
        item = self.value_list.currentItem()
        if item:
            self.value_list.editItem(item)

    def add_value(self):
        self._modified_tag().append("")
        item = QtGui.QListWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
        self.value_list.addItem(item)
        self.value_list.editItem(item)

    def remove_value(self):
        value_list = self.value_list
        row = value_list.row(value_list.currentItem())
        if row == 0 and self.different:
            self.different = False
            self.ui.add_value.setEnabled(True)
        value_list.takeItem(row)
        del self._modified_tag()[row]

    def disable_all(self):
        self.value_list.clear()
        self.value_list.setEnabled(False)
        self.ui.add_value.setEnabled(False)

    def enable_all(self):
        self.value_list.setEnabled(True)
        self.ui.add_value.setEnabled(True)

    def tag_changed(self, tag):
        tag_names = self.ui.tag_names
        row = tag_names.findText(tag, QtCore.Qt.MatchFixedString | QtCore.Qt.MatchCaseSensitive)
        tag_names.editTextChanged.disconnect(self.tag_changed)
        if row <= 0:
            self.disable_all()
            tag_names.setCurrentIndex(0)
            tag_names.setEditText(tag)
            self.tag = ""
        else:
            self.enable_all()
            tag_names.setCurrentIndex(row)
            self.tag = unicode(tag)
            self.value_list.clear()
            values = self.modified_tags.get(self.tag, None)
            if values is None:
                new_tags = self.metadata_box.tag_diff.new
                display_value, different = new_tags.display_value(self.tag)
                if different:
                    self.different = True
                    self._add_value_items([display_value], italic=True)
                    self.ui.add_value.setEnabled(False)
                    return
                values = new_tags[self.tag]
            self._add_value_items(values)
            self.value_list.setCurrentItem(self.value_list.item(0), QtGui.QItemSelectionModel.SelectCurrent)
        tag_names.editTextChanged.connect(self.tag_changed)

    def _add_value_items(self, values, italic=False):
        values = [v for v in values if v] or [""]
        for value in values:
            item = QtGui.QListWidgetItem(value)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
            font = item.font()
            font.setItalic(italic)
            item.setFont(font)
            self.value_list.addItem(item)

    def value_edited(self, item):
        row = self.value_list.row(item)
        value = unicode(item.text())
        if row == 0 and self.different:
            self.modified_tags[self.tag] = [value]
            self.different = False
            font = item.font()
            font.setItalic(False)
            item.setFont(font)
            self.ui.add_value.setEnabled(True)
        else:
            self._modified_tag()[row] = value

    def value_selection_changed(self):
        selection = len(self.value_list.selectedItems()) > 0
        self.ui.edit_value.setEnabled(selection)
        self.ui.remove_value.setEnabled(selection)

    def _modified_tag(self):
        return self.modified_tags.setdefault(self.tag,
               list(self.metadata_box.tag_diff.new[self.tag]) or [""])

    def accept(self):
        self.window.ignore_selection_changes = True
        for tag, values in self.modified_tags.items():
            self.modified_tags[tag] = [v for v in values if v]
        modified_tags = self.modified_tags.items()
        for obj in self.metadata_box.objects:
            for tag, values in modified_tags:
                obj.metadata._items[tag] = list(values) or [""]
            obj.update()
        self.window.ignore_selection_changes = False
        self.window.update_selection()
        QtGui.QDialog.accept(self)
