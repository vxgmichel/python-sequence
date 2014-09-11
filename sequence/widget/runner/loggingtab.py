# -*- coding: utf-8 -*-

""" Tab Widget to display a log console and a log table """

#-------------------------------------------------------------------------------
# Name:        LoggingTabWidget
# Purpose:     Tab Widget to display a log console and a log table
#
# Author:      michel.vincent
#
# Created:     21/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Imports
import os, sys
import logging
from PyQt4 import QtGui, QtCore


# Import from other packages
from sequence.widget.runner.control import ControlWidget
from sequence.widget.runner.log import LoggingWidget



# LoggingTabWidget Class Definition
class LoggingTabWidget(QtGui.QTabWidget):
    """
    Tab Widget to display a log console and a log table
    """
    def __init__(self, first_msg=None, *args, **kwargs):
        # Init tab widget
        super(LoggingTabWidget, self).__init__(*args, **kwargs)
        self.resize(800, 300)
        # Create console
        self.log_console = QtGui.QTextEdit(self)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(68, 68, 68))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(68, 68, 68))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        self.log_console.setPalette(palette)
        self.log_console.setFrameShadow(QtGui.QFrame.Sunken)
        self.log_console.setLineWidth(10)
        self.log_console.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.log_console.setReadOnly(True)
        self.log_console.setTabStopWidth(200)
        # Ugly HTML
        self.log_console.setHtml("""
<html>
<head>
<meta name=\"qrichtext\" content=\"1\" />
<style type=\"text/css\">
p, li { white-space: pre-wrap; }
</style>
</head>
<body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">
<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Consolas\'; font-size:10pt; color:#ffffff;\">
<br />
</p>
</body>
</html>
""")
        # Create table
        self.log_table = LoggingWidget(parent=self)
        # Add console
        self.addTab(self.log_console, "Console Logs")
        # Add table
        self.addTab(self.log_table, "Execution Logs")
        # Init stream
        self.eol = True
        # First write
        if first_msg:
            self.log(first_msg)

    def write(self, text):
        """
        Format the given string and write it in the console
        """
        # Format the string
        if not self.eol :
            string = QtCore.QString(text)
        else :
            string = '>>> '+ QtCore.QString(text)
        if len(text) > 0 and QtCore.QString(text)[-1] == '\n' :
            self.eol = True
        else :
            self.eol = False
        # Write it
        cursor = self.log_console.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(string)
        self.log_console.setTextCursor(cursor)

    def log(self, text, end='\n'):
        """
        Method to properly log a message
        """
        return self.write(unicode(text)+end)


# Main execution to test the widget
if __name__ == '__main__':
    import Packages
    app = QtGui.QApplication(sys.argv)
    ui1 = LoggingTabWidget("LoggingTabWidget Initialized.")
    ui1.show()
    ui2 = ControlWidget(log_signal = ui1.log)
    path = os.path.join(os.path.dirname(Packages.__file__),
                        os.pardir,
                        "Sequences",
                        "TempoFest.xml")
    ui2.set_path(path)
    ui2.enable()
    ui2.show()
    sys.stdout = ui1
    print("Test print : OK !")
    sys.exit(app.exec_())

