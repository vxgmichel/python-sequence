# -*- coding: utf-8 -*-

""" Module to handle sequences in the subsequence editor """

#-------------------------------------------------------------------------------
# Name:        SequenceItem
# Purpose:     Module to handle sequences in the subsequence editor
#
# Author:      michel.vincent
#
# Created:     21/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Imports
import os, types
from PyQt4 import QtGui, QtCore
from copy import deepcopy
from time import clock

# Imports from packages
from sequence.widget.editor.drawing import DrawingScene
from sequence.common.parser import parse_sequence_file, XMLSequence


# SequenceItem Class Definition
class SequenceItem(QtGui.QTreeWidgetItem):
    """
    Class representing a susequence item in the susequence editor
    """
    backup_icon = None
    sub_icon = None
    root_icon = None

    def __init__(self, parent, sequence, editor):
        """
        Initialize the sequence item
        with the QTreeWidget, the XML sequence reprensentation and the editor
        """
        # Init item
        super(SequenceItem, self).__init__(parent, [sequence.sequence_id])

        # Set attributes
        self.editor = editor
        self.sequence = sequence
        self.is_root = self.treeWidget() is parent
        self.is_backup = not self.is_root and parent.sequence.backup is sequence
        self.tab_widget = editor.ui.tab_widget
        self.double_clicked = False

        # Undo/Redo manager
        self.state_manager = UndoRedoManager(sequence.blocks,
                                             editor.ui.undo_button,
                                             editor.ui.redo_button)
        self.state_manager.update.connect(self.update)

        # Set flags
        flags = (QtCore.Qt.ItemIsSelectable|
                 QtCore.Qt.ItemIsEnabled |
                 QtCore.Qt.ItemIsEditable |
                 QtCore.Qt.ItemIsDropEnabled)
        if not self.is_root:
            flags |= QtCore.Qt.ItemIsDragEnabled
        self.setFlags(flags)
        if self.is_root:
            super_root = self.treeWidget().invisibleRootItem()
            super_root.setFlags(QtCore.Qt.NoItemFlags)

        # Recursive call
        for subsequence in self.sequence.subsequences:
                SequenceItem(self, subsequence, editor)

        # Set icon
        if self.root_icon is None:
            icon_path = QtCore.QString(u":/icons/icons/root-sequence.png")
            SequenceItem.root_icon = QtGui.QIcon(icon_path)
        if self.backup_icon is None:
            icon_path = QtCore.QString(u":/icons/icons/backup-sequence.png")
            SequenceItem.backup_icon = QtGui.QIcon(icon_path)
        if self.sub_icon is None:
            icon_path = QtCore.QString(u":/icons/icons/sequence.png")
            SequenceItem.sub_icon = QtGui.QIcon(icon_path)
        if self.is_root:
            icon = self.root_icon
        elif self.is_backup:
            icon = self.backup_icon
        else:
            icon = self.sub_icon
        self.setIcon(0, icon)

        # Tab creation
        self.tab_widget.currentChanged.connect(self.update_current)
        self.tab = QtGui.QWidget()
        self.scene = self.fill_tab()
        self.update(total=True)
        if self.is_root:
            self.on_edit()

        # Action creation
        self.action_new = QtGui.QAction('New', None)
        self.action_delete = QtGui.QAction('Delete', None)
        self.action_rename = QtGui.QAction('Rename', None)
        self.action_import = QtGui.QAction('Import', None)
        self.action_export = QtGui.QAction('Export as', None)
        self.action_edit = QtGui.QAction('Edit', None)
        self.action_backup = QtGui.QAction('Set as backup', None)
        self.action_backup.setCheckable(True)

        # Link actions
        self.action_new.triggered.connect(self.on_new)
        self.action_delete.triggered.connect(self.on_delete)
        self.action_rename.triggered.connect(self.on_rename)
        self.action_import.triggered.connect(self.on_import)
        self.action_export.triggered.connect(self.on_export)
        self.action_edit.triggered.connect(self.on_edit)
        self.action_backup.triggered.connect(self.on_backup)

        # Menu creation
        self.menu = QtGui.QMenu()
        self.menu.addAction(self.action_new)
        self.menu.addAction(self.action_delete)
        self.menu.addAction(self.action_rename)
        self.menu.addSeparator()
        self.menu.addAction(self.action_import)
        self.menu.addAction(self.action_export)
        self.menu.addSeparator()
        self.menu.addAction(self.action_edit)
        self.menu.addAction(self.action_backup)

    def log(self, text):
        """
        Send a logging message to the TreeWidget window
        """
        return self.treeWidget().window().log(text)

    def is_current(self):
        """
        Return True if the the sequence item corresponds to the current tab
        """
        if not hasattr(self, 'tab'):
            return False
        return self.tab_widget.currentWidget() is self.tab

    def on_undo(self):
        """
        Handle an undo signal
        """
        self.state_manager.undo()

    def on_redo(self):
        """
        Handle a redo signal
        """
        self.state_manager.redo()

    def update(self, total=False):
        """
        Update the sequence item
        """
        self.sequence.blocks = self.state_manager.get_current()
        self.scene.update(total)

    def set_changed(self):
        """
        Register a new state for the sequence item
        """
        self.state_manager.set_changed(self.sequence.blocks)

    def check_tree(self):
        """
        Update the tree structure
        """
        # Get list of sequence_id in the data model
        xml_ids = [sub.sequence_id for sub in self.sequence.subsequences]
        # Check for subsequence to add
        for index in range(self.childCount()):
            child = self.child(index)
            tree_id = child.sequence.sequence_id
            if tree_id in xml_ids:
                xml_ids.remove(tree_id)
            else:
                self.sequence.subsequences.append(child.sequence)
                child.setIcon(0, self.sub_icon)
                child.is_backup = False
        # Check for subsequence to remove
        for sub in list(self.sequence.subsequences):
            if sub.sequence_id in xml_ids:
                if self.sequence.backup and \
                   self.sequence.backup.sequence_id == sub.sequence_id:
                    self.sequence.backup = None
                self.sequence.subsequences.remove(sub)
                xml_ids.remove(sub.sequence_id)
        # Propagate
        for index in range(self.childCount()):
            self.child(index).check_tree()

    def update_current(self, index):
        """
        Make the font bold if the sequence item is the current tab
        """
        # Test if C/C++ object still exists
        try:
            self.font(0)
        # If not, disconnect the signal
        except RuntimeError as e:
            self.tab_widget.currentChanged.disconnect(self.update_current)
            return
        # Make the font bold if selected
        if self.tab_widget.indexOf(self.tab) == index:
            self.scene.update_block_model()
            font = self.font(0)
            font.setBold(True)
            self.setFont(0, font)
        # Otherwise, make it plain
        else :
            font = self.font(0)
            font.setBold(False)
            self.setFont(0, font)

    def update_menu(self):
        """
        Update the context menu
        """
        # Update actions
        if self.is_root:
            self.action_backup.setEnabled(False)
            self.action_delete.setEnabled(False)
        self.action_backup.setChecked(self.is_backup)

    def context_requested(self):
        """
        Return the context menu
        """
        self.update_menu()
        return self.menu

    ##### Signals slots #####

    def on_new(self, boolean=False):
        """
        Handle a subsequence creation
        """
        new_subsequence = XMLSequence("New Subsequence")
        self.sequence.subsequences.append(new_subsequence)
        item = SequenceItem(self, new_subsequence, self.editor)
        self.setExpanded(True)
        item.setText(0, u"")
        item.on_rename()
        self.editor.set_changed(True, global_change=True)

    def on_delete(self, boolean=False):
        """
        Handle a subsequence deletion
        """
        self.parent().sequence.subsequences.remove(self.sequence)
        self.parent().removeChild(self)
        self.tab_widget.removeTab(self.tab_widget.indexOf(self.tab))
        self.editor.set_changed(True, global_change=True)

    def on_rename(self, boolean=False):
        """
        Handle a subsequence renaming
        """
        self.treeWidget().editItem(self)
        edit_widget = self.treeWidget().itemWidget(self, 0)
        edit_widget.editingFinished.connect(self.apply_rename)

    def apply_rename(self):
        """
        Find and apply the new sequence id
        """
        # Disable signal for QLineEdit
        edit_widget = self.treeWidget().itemWidget(self, 0)
        if isinstance(edit_widget, QtGui.QLineEdit):
            edit_widget.editingFinished.disconnect()
        # Get id list
        if self.is_root:
            id_list = []
        else:
            id_list = [self.parent().child(index).sequence.sequence_id
                           for index in range(self.parent().childCount())
                               if self.parent().child(index) is not self]
        # Get the new id
        if edit_widget:
            sequence_id = unicode(edit_widget.text())
        else:
            sequence_id = unicode(self.text(0))
        if not sequence_id:
            sequence_id = self.sequence.sequence_id
        # Looking for a valid name
        if sequence_id in id_list:
            nb = 2
            if sequence_id.split()[-1].isdigit():
                nb = int(sequence_id.split()[-1])+1
                sequence_id = ' '.join(sequence_id.split()[:-1])
            current = sequence_id + ' ' + str(nb)
            while current in id_list:
                nb += 1
                current = sequence_id + ' ' + str(nb)
            sequence_id = current
        # Set the new id
        if self.sequence.sequence_id != sequence_id:
            self.editor.set_changed(True, global_change=True)
        self.sequence.sequence_id = sequence_id
        self.setText(0, sequence_id)
        # Set the tab name
        index = self.tab_widget.indexOf(self.tab)
        self.tab_widget.setTabText(index, sequence_id)

    def on_import(self, boolean=False):
        """
        Handle a subsequence import
        """
        # Get the path
        main = self.treeWidget().window()
        filename = unicode(QtGui.QFileDialog().getOpenFileName(main, "Import" ,
                                                               ".", "*.xml"))
        if filename == u"":
            return
        # Open the sequence
        self.file_path = os.path.abspath(filename)
        file_name = os.path.basename(self.file_path)
        self.log(u'IMPORT : {}'.format(file_name))
        try:
            subsequence = parse_sequence_file(self.file_path, execution=False)
        except StandardError as error:
            self.log('ERROR : '+ unicode(error))
            self.on_new()
            return
        self.sequence.subsequences.append(subsequence)
        item = SequenceItem(self, subsequence, self.editor)
        self.setExpanded(True)
        item.apply_rename()
        self.editor.set_changed(True, global_change=True)

    def on_export(self, boolean=False):
        """
        Export the selected subsequence as an xml file
        """
        # Get the path
        main = self.treeWidget().window()
        filename = unicode(QtGui.QFileDialog.getSaveFileName(main, 'Export',
                                                             '.', '*.xml'))
        if filename == u'':
            return
        # Export the sequence
        self.sequence.xml_export(filename)
        msg = self.sequence.sequence_id + u' -> ' + os.path.basename(filename)
        self.log(u'EXPORT : ' + msg)

    def on_edit(self, boolean=False):
        """
        Open and display the sequence item in a tab
        """
        # Tab handling
        if self.tab_widget.indexOf(self.tab) == -1:
            self.tab_widget.addTab(self.tab, self.sequence.sequence_id)
        self.tab_widget.setCurrentWidget(self.tab)
        self.tab_widget.tabBar().tabButton(0,1).resize(0, 0)
        self.state_manager.update_buttons()

    def on_backup(self, boolean=False):
        """
        Toogle the backup status of the sequence item
        """
        # Toogle status
        self.is_backup = not self.is_backup
        # Update
        if self.is_backup:
            for index in range(self.parent().childCount()):
                self.parent().child(index).is_backup = False
                self.parent().child(index).setIcon(0, self.sub_icon)
            self.is_backup = True
            self.parent().sequence.backup = self.sequence
            self.setIcon(0, self.backup_icon)
        else:
            self.parent().sequence.backup = None
            self.setIcon(0, self.sub_icon)
        self.editor.set_changed(True, global_change=True)

    def fill_tab(self):
        """
        Create the drawing area corresponding to the sequence item
        """
        # Create drawing area
        drawing_area = QtGui.QGraphicsView(self.tab)
        drawing_area.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                       QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        hfw = drawing_area.sizePolicy().hasHeightForWidth()
        sizePolicy.setHeightForWidth(hfw)
        drawing_area.setSizePolicy(sizePolicy)
        drawing_area.setBaseSize(QtCore.QSize(0, 0))
        drawing_area.setMouseTracking(True)
        drawing_area.setAcceptDrops(True)
        drawing_area.setFrameShape(QtGui.QFrame.NoFrame)
        drawing_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        drawing_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        drawing_area.setRenderHints(QtGui.QPainter.Antialiasing|
                                    QtGui.QPainter.TextAntialiasing)
        drawing_area.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        drawing_area.setResizeAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        # Create layout
        gridLayout = QtGui.QGridLayout(self.tab)
        gridLayout.setMargin(0)
        gridLayout.addWidget(drawing_area, 0, 0, 1, 1)
        # Create scene
        drawing_scene = DrawingScene(drawing_area, self)
        drawing_area.setScene(drawing_scene)
        return drawing_scene


class UndoRedoManager(QtCore.QObject):
        """
        Inner class to manage undo and redo operation
        """
        # Time reference for change detection
        delta_ref = 0.05

        # Signal to update the current object
        update = QtCore.pyqtSignal()

        def __init__(self, current, undo_button, redo_button):
            """
            Initialize the manager with the current state and the buttons
            """
            QtCore.QObject.__init__(self)
            self.doing = False
            self.undo_list = []
            self.redo_list = []
            self.last_change = clock()
            self.redo_button = redo_button
            self.undo_button = undo_button
            self.reset(current)

        def reset(self, current):
            """
            Reset the manager using the current sequence
            """
            self.undo_list = [deepcopy(current)]
            self.redo_list = []
            self.doing = False
            self.last_change = clock()

        def set_changed(self, current):
            """
            Update the manager using the current sequence
            """
            # Compute delta
            delta = self.last_change
            self.last_change = clock()
            delta = self.last_change - delta
            # Save state
            if not self.doing and delta > self.delta_ref:
                self.undo_list.append(deepcopy(current))
                if len(self.undo_list) > 1:
                    self.undo_button.setEnabled(True)
                self.redo_list = []
                self.redo_button.setEnabled(False)
            elif not self.doing:
                self.undo_list[-1] = deepcopy(current)

        def update_buttons(self):
            """
            Update the buttons status
            """
            self.undo_button.setEnabled(len(self.undo_list) > 1)
            self.redo_button.setEnabled(bool(self.redo_list))

        def undo(self):
            """
            Undo the last action
            """
            if len(self.undo_list) > 1:
                self.redo_button.setEnabled(True)
                self.redo_list.append(self.undo_list.pop())
                self.doing = True
                self.update.emit()
                self.doing = False
            if not len(self.undo_list) > 1:
                self.undo_button.setEnabled(False)

        def redo(self):
            """
            Cancel the last undo action
            """
            if self.redo_list:
                self.undo_button.setEnabled(True)
                self.undo_list.append(self.redo_list.pop())
                self.doing = True
                self.update.emit()
                self.doing = False
            if not self.redo_list:
                self.redo_button.setEnabled(False)

        def get_current(self):
            """
            Get the current object
            """
            return deepcopy(self.undo_list[-1])
