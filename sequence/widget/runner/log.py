# -*- coding: utf-8 -*-

""" Widget to display execution logs from Sequence Engines """

#-------------------------------------------------------------------------------
# Name:        LoggingWidget
# Purpose:     Widget to display execution logs from Sequence Engines
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

# Import from sequence
from sequence.core.engine import add_log_handler
from sequence.widget.runner.control import ControlWidget


# Signal Handler class definition
class SignalHandler(QtCore.QObject):
    """
    Class to bind PyQtSignal and the logging module
    """
    signal = QtCore.pyqtSignal(logging.LogRecord)

    def __init__(self, level=logging.INFO, *args, **kwargs):
        super(SignalHandler, self).__init__(*args, **kwargs)
        self.level = level

    def handle(self, log_record):
        self.signal.emit(log_record)


# Custom Delegate Class Definition
class CustomDelegate(QtGui.QStyledItemDelegate):
    """
    Custom Delegate to clear the grey focus rectangle
    """
    def paint(self, painter, option, index):
        """
        Override the paint method
        """
        option.state &= ~QtGui.QStyle.State_HasFocus
        QtGui.QStyledItemDelegate.paint(self, painter, option, index)


# Log Record Item Class Definition
class LogRecordItem():
    """
    Class to handle a Log Record as a row
    """

    def __init__(self, log_record, nb):
        """
        Init method with the log record informations
        """
        # Get record informations
        self.nb = "{:7}".format(nb)
        time = u'{:8},{:03}'
        secs = logging.Formatter().formatTime(log_record, '%H:%M:%S')
        self.time = time.format(secs, int(log_record.msecs))
        self.thread = log_record.threadName
        self.sequence = log_record.sequenceID
        self.type = log_record.type
        self.block_id = log_record.ID
        self.level = log_record.levelname
        self.message = u""
        if log_record.msg:
            self.message = log_record.msg
        # Create items
        values = [self.nb, self.time, self.thread, self.sequence,
                  self.type, self.block_id, self.level, self.message]
        self.items = []
        for i, value in enumerate(values):
            item = QtGui.QTableWidgetItem(unicode(value), 0)
            item.parent = self
            item.setFlags(QtCore.Qt.ItemIsEnabled |
                          QtCore.Qt.ItemIsSelectable)
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self.items.append(item)

    def set_selected(self, boolean):
        """
        Select or unselect the Tango Event with a boolean
        """
        for item in self:
            item.setSelected(boolean)

    def row(self):
        """
        Return the row number of the Tango Event
        """
        return self.items[0].row()

    def __iter__(self):
        """
        Return an iterator of the items
        """
        return iter(self.items)


# MainWidget Class Definition
class LoggingWidget(QtGui.QTableWidget):
    """
    Widget to display execution logs from Sequence Engines
    """
    # Init method
    def __init__(self, level=logging.INFO, parent=None):
        # Initialize with parent class
        QtGui.QTableWidget.__init__(self, parent)
        # Customize widget
        self.resize(778, 277)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        column_names = [u"Nb", u"Date", u"Thread", u"Sequence",
                        u"Type", u"ID", u"Level", u"Message"]
        self.setColumnCount(len(column_names))
        self.setRowCount(0)
        for i, name in enumerate(column_names):
            item = QtGui.QTableWidgetItem(name)
            self.setHorizontalHeaderItem(i, item)
        mode = QtGui.QHeaderView.ResizeToContents
        self.horizontalHeader().setResizeMode(mode)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().hide()
        self.setItemDelegate(CustomDelegate())
        palette = self.palette()
        name = QtGui.QPalette.AlternateBase
        color = QtCore.Qt.lightGray
        palette.setColor(name, color)
        self.setPalette(palette)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.verticalHeader().setDefaultSectionSize(30)
        # Init attributes
        self.signal_handler = SignalHandler(level)
        self.signal_handler.signal.connect(self.handle_log_record)
        add_log_handler(self.signal_handler)
        self.log_items = []
        self.log_count = 0

    #### Signal handling ####

    def mousePressEvent(self, event):
        """
        Handle the right click on an item
        """
        # Return if not a right click
        QtGui.QTableWidget.mousePressEvent(self, event)
        if event.button() == QtCore.Qt.LeftButton and \
            event.modifiers() == QtCore.Qt.ControlModifier:
             self.itemAt(self.pos()).setSelected(True)
        if event.button() != QtCore.Qt.RightButton:
            return
        # Create lists
        items = self.selectedItems()
        log_items = list({item.parent for item in items
                            if isinstance(item.parent, LogRecordItem)})
        # Create menu
        menu = QtGui.QMenu()
        action_clear = QtGui.QAction("Clear", menu)
        action_clear_all = QtGui.QAction("Clear All", menu)
        if log_items:
            menu.addAction(action_clear)
        menu.addAction(action_clear_all)
        res = menu.exec_(event.globalPos())
        # Get result
        if res is action_clear:
            for item in log_items:
                self.remove_log_item(item)
                self.log_items.remove(item)
        elif res is action_clear_all:
            self.clearContents()
            self.setRowCount(0)
            self.log_items = []
            self.log_count = 0
        for item in self.log_items:
            item.set_selected(False)

    def sizeHintForColumn(self, column):
        """
        Override original method to resize all the columns
        """
        fm = self.fontMetrics()
        max_width = 0
        for i in range(self.rowCount()):
            width = fm.width(self.item(i,column).text()) + 10
            if  width > max_width:
                max_width = width
        return max_width

    def handle_log_record(self, log_record):
        """
        Handle log record from the logging module
        """
        # Create log item
        log_item = LogRecordItem(log_record, self.log_count)
        # Increment log counter
        self.log_count += 1
        # Update
        self.add_log_item(log_item)

    def add_log_item(self, log_item):
        """
        Add a log item to the widget
        """
        self.log_items.append(log_item)
        i = self.rowCount()
        self.insertRow(i)
        for j, item in enumerate(log_item):
            self.setItem(i, j, item)

    def remove_log_item(self, item):
        """
        Remove a Tango Event from the widget
        """
        self.removeRow(item.row())


# Main execution to test the widget
if __name__ == '__main__':
    import sequence
    app = QtGui.QApplication(sys.argv)

    def print_in_console(msg, end):
        sys.stdout.write(msg + end)
        sys.stdout.flush()

    ui1 = ControlWidget(log_signal=print_in_console)
    path = os.path.join(os.path.dirname(sequence.__file__),
                        os.pardir,
                        "examples",
                        "BranchTest.xml")
    ui1.set_path(path)
    ui1.enable()
    ui1.show()
    ui2 = LoggingWidget()
    ui2.show()
    sys.exit(app.exec_())
