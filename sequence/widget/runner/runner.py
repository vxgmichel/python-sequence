# -*- coding: utf-8 -*-

""" Widget for running and monitoring sequences """

#-------------------------------------------------------------------------------
# Name:        RunnerWidget
# Purpose:     Widget for running and monitoring sequences
#
# Author:      michel.vincent
#
# Created:     21/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Imports
import locale
import os, sys
import logging
import subprocess
from PyQt4 import QtGui, QtCore


# Import from other packages
from sequence.widget.runner.control import ControlWidget
from sequence.widget.runner.loggingtab import LoggingTabWidget


class RunnerWidget(QtGui.QWidget):
    """
    Widget for running and monitoring sequences
    """
    size_changed = QtCore.pyqtSignal()
    hspace = 10
    vspace = 5
    base_size = 800,300

    def __init__(self, *args, **kwargs):
        # Init GroupBox
        super(RunnerWidget, self).__init__(*args, **kwargs)
        self.resize(*self.base_size)
        self.saved_height = self.base_size[1]

        # Fist line
        self.vbox_layout = QtGui.QVBoxLayout(self)
        hbox_layout = QtGui.QHBoxLayout()
        self.filename_edit = QtGui.QLineEdit(self)
        self.select_button = QtGui.QPushButton(u'Select', self)
        self.edit_button = QtGui.QPushButton(u'Edit', self)
        self.new_button = QtGui.QPushButton(u'New', self)
        hbox_layout.addWidget(self.filename_edit, 1)
        hbox_layout.addWidget(self.select_button)
        hbox_layout.addSpacing(self.hspace)
        line = QtGui.QFrame(self)
        line.setFrameShape(QtGui.QFrame.VLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        hbox_layout.addWidget(line)
        hbox_layout.addSpacing(self.hspace)
        hbox_layout.addWidget(self.edit_button)
        hbox_layout.addWidget(self.new_button)
        self.vbox_layout.addLayout(hbox_layout)
        self.vbox_layout.addSpacing(self.vspace)

        # Second line
        hbox_layout = QtGui.QHBoxLayout()
        hbox_layout.addWidget(QtGui.QLabel(u"Display Console:"))
        self.check_box = QtGui.QCheckBox(self)
        self.check_box.setChecked(True)
        hbox_layout.addWidget(self.check_box)
        hbox_layout.addStretch(1)
        hbox_layout.addSpacing(self.hspace)
        hbox_layout.addWidget(QtGui.QLabel(u"Sequence Control :"))
        hbox_layout.addSpacing(self.hspace)

        # Create control widget
        self.control_widget = ControlWidget(parent=self)
        self.control_widget.enable_path_request()
        self.control_widget.disable()
        hbox_layout.addWidget(self.control_widget)

        # Create logging tab
        self.logging_tab = LoggingTabWidget("CONSOLE INITIALIZED",
                                            parent=self)
        self.logging_tab.setTabPosition(QtGui.QTabWidget.South)
        self.logging_tab.log_table.verticalHeader().setDefaultSectionSize(20)
        self.logging_tab.setVisible(True)
        self.vbox_layout.addLayout(hbox_layout)
        self.vbox_layout.addSpacing(self.vspace)
        self.vbox_layout.addWidget(self.logging_tab)
        self.setLayout(self.vbox_layout)

        # Connect signals
        self.select_button.clicked.connect(self.on_select)
        self.check_box.stateChanged.connect(self.on_display_console)
        self.control_widget.log_signal.connect(self.logging_tab.log)
        self.control_widget.path_requested.connect(self.on_path_requested)
        self.filename_edit.textChanged.connect(self.on_path_changed)
        self.new_button.clicked.connect(self.open_editor)
        def open_with_file(_):
            return self.open_editor(True, self.filename_edit.text())
        self.edit_button.clicked.connect(open_with_file)
        if self.isWindow():
            self.size_changed.connect(self.custom_resize)

    def on_select(self):
        """
        Select a sequence
        """
        path = os.getcwd()
        filename = unicode(QtGui.QFileDialog.getOpenFileName(self,
                                                             'Select Sequence',
                                                             path, '*.xml'))
        if filename == u"":
            return
        self.filename_edit.setText(filename)

    def on_path_requested(self):
        """
        Load a file with the filename in the LineEdit
        """
        self.control_widget.load(self.filename_edit.text())

    def on_path_changed(self, text):
        """
        Disable the control widget if the given filename is emprty
        """
        self.control_widget.disable()
        if text:
            self.control_widget.enable()

    def set_filename(self, filename):
        """
        Set the given filname in the LineEdit
        """
        filename = os.path.abspath(filename)
        self.filename_edit.setText(filename)

    def on_display_console(self, boolean):
        """
        Display or hide the logging tab widget with a given boolean
        """
        self.logging_tab.setVisible(boolean)
        self.vbox_layout.itemAt(3).changeSize(0, bool(boolean)*self.vspace)
        self.vbox_layout.activate()
        self.size_changed.emit()

    def custom_resize(self):
        """
        Resize the widget consering the visibility of the logging tab widget
        """
        width = self.size().width()
        height = self.size().height()
        if self.logging_tab.isVisible():
            height = self.saved_height
        else:
            self.saved_height = height
            height = 0
        self.resize(width, height)

    def open_editor(self, boolean, filename=""):
        """
        Open the editor in a subprocess
        The given filename is used to open a sequence
        """
        cmd = u'python -m sequence.editor '
        if filename:
            cmd += ' ' + filename
        cmd = cmd.encode(locale.getpreferredencoding())
        try:
            subprocess.Popen(cmd, shell=True)
        except OSError as e:
            print e.strerror

    def set_display_console(self, boolean):
        """
        Set the console display mode
        """
        self.check_box.setChecked(boolean)


# Main Execution
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ui = RunnerWidget()
    ui.show()
    sys.exit(app.exec_())
