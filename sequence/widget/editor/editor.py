# -*- coding: utf-8 -*-

""" Main module for the block sequence editor """

#-------------------------------------------------------------------------------
# Name:        EditorWidget
# Purpose:     Main module for the sequence editor
#
# Author:      michel.vincent
#
# Created:     21/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Imports
import sequence
import os, sys, types
from PyQt4 import QtGui, QtCore
from functools import partial
import logging

# Imports from SequenceEditor package
from sequence.widget.editor.item import SequenceItem
from sequence.widget.editor.blockmodel import BlockModel
from sequence.resource.pyqt.editor_ui import Ui_PySequenceEditor


# Import from other packages
from sequence.action.abstract import get_action_list
from sequence.common.constant import XBM, IMAGES_DIR
from sequence.common.parser import parse_sequence_file, XMLSequence
from sequence.core.engine import add_log_handler

from sequence.widget.runner.control import ControlWidget
from sequence.widget.runner.loggingtab import LoggingTabWidget




# Signal Handler class definition
class SignalHandler(QtCore.QObject):
    """
    Class to bind PyQtSignal and the logging module
    """
    signal = QtCore.pyqtSignal(logging.LogRecord)

    def __init__(self, level=logging.DEBUG, *args, **kwargs):
        super(SignalHandler, self).__init__(*args, **kwargs)
        self.level = level

    def handle(self, log_record):
        self.signal.emit(log_record)


# EditorWidget Class Definition
class EditorWidget(QtGui.QWidget):
    """
    Main class of the PySequence Editor
    """

    def __init__(self, parent=None):
        # Setup UI
        super(EditorWidget, self).__init__(parent)
        self.ui = Ui_PySequenceEditor()
        self.ui.setupUi(self)

        # Customize UI
        self.ui.main_splitter.setStretchFactor(1, 1)
        self.ui.center_splitter.setStretchFactor(0, 1)
        self.logging_tab = LoggingTabWidget(parent=self)
        self.logging_tab.setTabPosition(QtGui.QTabWidget.South)
        self.logging_tab.log_table.verticalHeader().setDefaultSectionSize(20)
        self.logging_tab.resize(0,0)
        self.ui.center_splitter.addWidget(self.logging_tab)
        self.ui.tab_widget.clear()
        self.control_widget = ControlWidget(parent=self)
        self.ui.horizontalLayout.insertWidget(13, self.control_widget)

        # Monkey Patching
        def dropEvent(self, event):
            QtGui.QTreeWidget.dropEvent(self, event)
            self.currentItemChanged.emit(None, None)
        sub_editor = self.ui.subsequence_editor
        sub_editor.dropEvent = types.MethodType(dropEvent, sub_editor)

        # Stream redirection
        self.save_stdout = sys.stdout
        self.save_stderr = sys.stderr
        sys.stdout = self.logging_tab
        sys.stderr = self.logging_tab

        # Sequence Engine
        self.control_widget.enable_path_request()
        self.control_widget.path_requested.connect(self.on_path_requested)
        self.control_widget.log_signal.connect(self.log)

        # Property editor initialization
        self.block_model = BlockModel(self, parent=self.ui.property_editor)
        self.block_model.model_changed.connect(partial(self.set_changed, True))
        self.ui.property_editor.setModel(self.block_model)

        # Create block Mapping
        self.block_mapping = {"Begin/End":   {'Begin':  XBM.BEGIN,
                                              'End'  :  XBM.END},
                              "Time":        {'Init':   XBM.TIMEINIT,
                                              'Wait':   XBM.WAIT},
                              "Branch":      {'Branch': XBM.BRANCH},
                              "Subsequence": {'Macro':  XBM.MACRO}}
        action_list = get_action_list()
        self.module_to_name = {module: name for name, module in action_list}
        for name, module in action_list:
            family = module.split(".")[-2].capitalize()
            self.block_mapping.setdefault(family, {})[name] = (XBM.ACTION, module)


        # Block list initialization
        self.ui.block_list.setHeaderLabels(['Block list'])
        self.fill_block_list()
        self.ui.block_list.expandAll()
        self.ui.block_list.resizeColumnToContents(0)
        self.ui.block_list.expandToDepth(0)

        # Sequence initialization
        self.current_sequence = XMLSequence("New Sequence")

        # Signals connection
        self.ui.open_button.clicked.connect(self.on_open)
        self.ui.new_button.clicked.connect(self.on_new)
        self.ui.save_button.clicked.connect(self.on_save)
        self.ui.save_as_button.clicked.connect(self.on_save_as)
        self.ui.undo_button.clicked.connect(self.on_undo)
        self.ui.redo_button.clicked.connect(self.on_redo)
        self.ui.about_button.clicked.connect(self.on_about)
        self.ui.zoom_slider.valueChanged.connect(self.on_change_zoom_value)
        self.ui.block_list.itemClicked.connect(self.on_click_family)
        self.ui.tab_widget.tabCloseRequested.connect(self.on_close_tab)
        self.ui.tab_widget.currentChanged.connect(self.update_zoom_slider)
        sub_editor = self.ui.subsequence_editor
        sub_editor.itemDoubleClicked.connect(self.subsequence_double_clicked)
        sub_editor.itemActivated.connect(self.subsequence_activated)
        sub_editor.customContextMenuRequested.connect(self.context_requested)
        sub_editor.currentItemChanged.connect(self.subsequence_changed)
        QtGui.QShortcut(QtGui.QKeySequence.SelectAll, self, self.on_select_all)

        # Update
        self.file_path = None
        self.changed = False
        self.set_changed(False)
        self.update()

        # Logging
        self.log(u'PySequence Editor Initialized.')


        self.signal_handler = SignalHandler(logging.DEBUG)
        self.signal_handler.signal.connect(self.handle_log_record)
        add_log_handler(self.signal_handler)


    def handle_log_record(self, log_record):
        """
        Handle log record from the logging module
        """
        if log_record.levelno != logging.DEBUG:
            return
        sub_editor = self.ui.subsequence_editor
        flags = QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive
        seq_item = sub_editor.findItems(u"{}".format(log_record.sequenceID),
                                        flags)[0]
        if not seq_item:
            return
        block_id = log_record.ID
        bes = log_record.msg
        for block in seq_item.scene.block_list:
            if block.xml_block.block_id == block_id:
                block.set_execution_state(bes)
                break


    #### Generate block list ####

    def fill_block_list(self):
        """
        Fill the block list with common blocks and action blocks
        """
        for family in sorted(self.block_mapping):
            family_item = QtGui.QTreeWidgetItem(self.ui.block_list, [family])
            family_item.setFlags(QtCore.Qt.ItemIsEnabled)

            for model in sorted(self.block_mapping[family]):
                model_item = QtGui.QTreeWidgetItem(family_item, [model])
                model_item.setFlags(QtCore.Qt.ItemIsSelectable|
                                   QtCore.Qt.ItemIsEnabled|
                                   QtCore.Qt.ItemIsDragEnabled)
                data = self.block_mapping[family][model]
                if not isinstance(data, tuple):
                    model = data
                url = os.path.join(IMAGES_DIR, model)
                image = QtGui.QPixmap(url)
                if image.isNull():
                    url = os.path.join(IMAGES_DIR, 'Undefined')
                    image = QtGui.QPixmap(url)
                image = image.scaled(64, 64,
                                     QtCore.Qt.KeepAspectRatio,
                                     QtCore.Qt.SmoothTransformation)
                model_item.setIcon(0, QtGui.QIcon(image))

    ##### Update method #####

    def update(self):
        """
        Get the up-to-date data model and update the graphics
        """
        # Clear tabs
        self.ui.tab_widget.clear()
        # Subsequence Editor
        self.ui.subsequence_editor.clear()
        SequenceItem(self.ui.subsequence_editor, self.current_sequence, self)
        self.ui.subsequence_editor.expandAll()

    ##### File handling signals #####

    def on_path_requested(self):
        if self.changed:
            msg = "Source not saved \nSave before loading?"
            res = QtGui.QMessageBox.question(self, 'Save before loading', msg,
                                            QtGui.QMessageBox.Yes,
                                            QtGui.QMessageBox.Cancel)
            if res == QtGui.QMessageBox.Cancel or not self.on_save():
                return
        self.control_widget.load(self.file_path)

        sub_editor = self.ui.subsequence_editor
        flags = QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive
        for item in sub_editor.findItems(u"", flags):
            item.scene.reset_execution_state()

    def on_new(self):
        """
        Create a new sequence
        """
        # Reset control
        if not self.control_widget.reset():
            return
        self.control_widget.disable()
        # Create new sequence
        self.file_path = None
        self.set_changed(False)
        self.current_sequence = XMLSequence("New Sequence", depth=0,
                                            level=0, execution=False)
        # Update
        self.update()
        self.log('NEW : New Sequence')

    def on_open(self):
        """
        Display a dialogue to open a sequence
        """
        # Stop control widget
        if not self.control_widget.reset():
            return
        # Get the filename
        filename = unicode(QtGui.QFileDialog().getOpenFileName(self, "Open" ,
                                                               ".", "*.xml"))
        if filename == u"":
            return
        return self.open(filename)

    def open(self, filename):
        """
        Open a sequence from an XML file
        """
        # Open the sequence
        self.file_path = os.path.abspath(filename)
        file_name = os.path.basename(self.file_path)
        self.log(u'OPEN : {}'.format(file_name))
        try:
            self.current_sequence = parse_sequence_file(self.file_path,
                                                        execution=False)
        except StandardError as error:
            self.log('ERROR : '+ repr(error))
            self.on_new()
            return
        # Update
        self.update()
        # No changes
        self.set_changed(False)

    def on_save(self):
        """
        Save changed of the current sequence
        """
        # Already saved case
        if not self.changed and self.file_path:
            return
        # No file path case
        if not self.file_path:
            filename = unicode(QtGui.QFileDialog.getSaveFileName(self, 'Save',
                                                                 '.', '*.xml'))
            if filename == u'':
                return False
            self.file_path = os.path.abspath(filename)
        # Save the sequence
        self.set_changed(False)
        self.current_sequence.xml_export(self.file_path)
        file_name = os.path.basename(self.file_path)
        sequence_id = self.current_sequence.sequence_id
        self.log(u'SAVE : {} ({})'.format(file_name, sequence_id))
        return True

    def on_save_as(self):
        """
        Save the current sequence in an xml file
        """
        # Started engine case
        if not self.control_widget.reset():
            return
        # Get the new path
        filename = unicode(QtGui.QFileDialog.getSaveFileName(self, 'Save as',
                                                             '.', '*.xml'))
        if filename == u'':
            return False
        # Save the sequence
        self.set_changed(False)
        self.file_path = filename
        self.current_sequence.xml_export(self.file_path)
        file_name = os.path.basename(self.file_path)
        sequence_id = self.current_sequence.sequence_id
        self.log(u'SAVE AS : {} ({})'.format(file_name, sequence_id))
        return True

    #### About button signal ####

    def on_about(self):
        """
        Display "About" informations
        """
        msg = u'''
        <b>Sequence Editor</b><br/>
        <br/>
        Version 1.0.0
        <p>
            Sequence Editor is an application for designing,
            editing and testing action block sequences.
        </p>
        <br/>
        <br/>
        <b>Author</b> : <a href="http://www.nexeya.fr/">NEXEYA SYSTEM</a>
        '''
        url = QtCore.QString(u":/logos/logos/nexeya_logo.png")
        image = QtGui.QPixmap(url).scaled(128,
                                          128,
                                          QtCore.Qt.KeepAspectRatio,
                                          QtCore.Qt.SmoothTransformation)
        about = QtGui.QMessageBox(QtGui.QMessageBox.Information, "About", msg)
        about.setIconPixmap(image)
        mbi = QtGui.QStyle.SP_MessageBoxInformation
        icon = QtGui.QApplication.style().standardIcon(mbi)
        about.setWindowIcon(icon)
        about.exec_()

    #### Scene signals ####

    def on_select_all(self):
        """
        Select all items in scene
        """
        for item in self.drawing_scene.items():
            item.setSelected(True)

    def on_change_zoom_value(self, value):
        """
        Set a new zoom value
        """
        if value > 91 and value < 109:
            value = 100
        self.ui.zoom_slider.setValue(value)
        self.ui.zoom_label.setText("{}%".format(value))
        current_area = self.get_current_sequence_item().scene.parent()
        current_area.resetTransform()
        current_area.scale(float(value)/100, float(value)/100)

    def update_zoom_slider(self):
        """
        Update the zoom slider
        """
        current_item = self.get_current_sequence_item()
        if not current_item:
            return
        value = current_item.scene.parent().transform().m11()*100
        self.ui.zoom_slider.setValue(value)

    #### Block list signals ####

    @staticmethod
    def on_click_family(item, _):
        """
        Toogle the item expandation
        """
        if item.childCount():
            item.setExpanded(not item.isExpanded())

    #### Tab widget signals ####

    def on_close_tab(self, index):
        """
        Close a tab
        """
        self.ui.tab_widget.removeTab(index)

    #### Sequence Browser signals ####

    @staticmethod
    def subsequence_double_clicked(item, _):
        """
        Handle the subsequence double click
        """
        item.double_clicked = True

    @staticmethod
    def subsequence_activated(item, _):
        """
        Handle the subsequence activation
        """
        if item.double_clicked:
            item.double_clicked = False
            item.on_edit()
        else:
            item.on_rename()

    def subsequence_changed(self, old, new):
        """
        Update sequence tree when data changed
        """
        if old is None and new is None:
            super_root = self.ui.subsequence_editor.invisibleRootItem()
            super_root.child(0).check_tree()

    def context_requested(self, point):
        """
        Display a context menu when requested
        """
        item = self.ui.subsequence_editor.itemAt(point)
        if not item:
            return
        menu = item.context_requested()
        menu.exec_(self.ui.subsequence_editor.mapToGlobal(point))

    ##### Handle modifications #####

    def get_current_sequence_item(self):
        """
        Get the current sequence item
        """
        sub_editor = self.ui.subsequence_editor
        flags = QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive
        for item in sub_editor.findItems(u"", flags):
            if item.is_current():
                return item

    def on_undo(self):
        """
        Undo the last action of the current tab
        """
        return self.get_current_sequence_item().on_undo()

    def on_redo(self):
        """
        Redo the last action of the current tab
        """
        return self.get_current_sequence_item().on_redo()

    def set_changed(self, value, global_change=False):
        """
        Update the main widget depending on whether or not the file is UtD
        If value is False, the file is up-to-date, True otherwise
        """
        self.changed = value
        # Undo redo mecanism
        if value and not global_change:
            current_sub_item = self.get_current_sequence_item()
            if current_sub_item:
                current_sub_item.set_changed()
        # Enable the load button
        if self.file_path or self.changed:
            self.control_widget.enable()
        # Set name to display
        if self.file_path:
            name = os.path.basename(self.file_path)
        else:
            name = self.current_sequence.sequence_id
        title = 'PySequence Editor - '
        # Set the title format
        if self.changed:
            title += '*' + name + '*'
        else:
            title += name
        # Set the window title
        self.setWindowTitle(title)

    #### Log method ####

    def log(self, msg, end="\n"):
        """
        Method to properly log a message
        """
        return self.logging_tab.log(msg, end)

    #### Close Event ####

    def closeEvent(self, event):
        """
        Override closeEvent to handle secial cases
        """
        # Stop control widget
        if not self.control_widget.reset():
            return event.ignore()
        # Sequence not saved case
        if self.changed:
            msg = "Source not saved \nSave before closing?"
            res = QtGui.QMessageBox.question(self, 'Save before closing', msg,
                                            QtGui.QMessageBox.Yes,
                                            QtGui.QMessageBox.No,
                                            QtGui.QMessageBox.Cancel)
            if res == QtGui.QMessageBox.Cancel or \
               (res == QtGui.QMessageBox.Yes and not self.on_save()):
                return event.ignore()
        # Put the original streams back in place
        sys.stdout = self.save_stdout
        sys.stderr = self.save_stderr


