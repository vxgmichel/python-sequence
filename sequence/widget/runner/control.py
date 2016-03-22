# -*- coding: utf-8 -*-

""" Widget to control a Sequence Engine """

#-------------------------------------------------------------------------------
# Name:        ControlWidget
# Purpose:     Widget to control a sequence engine
#
# Author:      michel.vincent
#
# Created:     21/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Imports
import os, sys, logging
from PyQt4 import QtGui, QtCore

# Imports from sequence
from sequence.resource.pyqt import control_icons_rc
from sequence.core.engine import SequenceEngine


# MainWidget Class Definition
class ControlWidget(QtGui.QWidget):
    """
    Widget to control a Sequence Engine
    """

    # Class signals
    path_requested = QtCore.pyqtSignal()
    log_signal = QtCore.pyqtSignal([unicode, unicode])
    execution_started = QtCore.pyqtSignal()
    execution_finished = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        # Init widget
        super(ControlWidget, self).__init__(*args, **kwargs)
        # Create load button
        self.load_button = QtGui.QToolButton(self)
        url = u":/control_icons/icons/go-bottom.png"
        self.load_button.setIcon(QtGui.QIcon(url))
        self.load_button.setIconSize(QtCore.QSize(32, 32))
        self.load_button.clicked.connect(self.on_load)
        self.load_button.setShortcut(QtGui.QKeySequence("F5"))
        self.load_button.setToolTip("Load the sequence (F5)")
        # Create run button
        self.run_button = QtGui.QToolButton(self)
        url = u":/control_icons/icons/go-next.png"
        self.run_button.setIcon(QtGui.QIcon(url))
        self.run_button.setIconSize(QtCore.QSize(32, 32))
        self.run_button.clicked.connect(self.on_run)
        self.run_button.setShortcut(QtGui.QKeySequence("F6"))
        self.run_button.setToolTip("Run the sequence (F6)")
        # Create stop button
        self.stop_button = QtGui.QToolButton(self)
        url = u":/control_icons/icons/process-stop.png"
        self.stop_button.setIcon(QtGui.QIcon(url))
        self.stop_button.setIconSize(QtCore.QSize(32, 32))
        self.stop_button.clicked.connect(self.on_stop)
        self.stop_button.setShortcut(QtGui.QKeySequence("F7"))
        self.stop_button.setToolTip("Stop the sequence (F7)")
        # Create layout
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.load_button)
        self.layout.addWidget(self.run_button)
        self.layout.addWidget(self.stop_button)
        # Init attributes
        self.layout.setMargin(0)
        self.engine = SequenceEngine()
        self.enabled = False
        self.file_path = ""
        self.path_request_enabled = False
        self.disable()

    #### Base methods ####

    def enable_path_request(self):
        """ Enable the path requested signal to load file """
        self.path_request_enabled = True

    def disable_path_request(self):
        """ Disable the path requested signal to load file """
        self.path_request_enabled = False

    def set_path(self, path):
        """ Set the path of the file to load """
        if path:
            self.file_path = unicode(path)

    def disable(self):
        """
        Disable the control of the sequence engine
        """
        self.enabled = False
        self.load_button.setEnabled(False)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(False)

    def enable(self):
        """
        Enable the control of the sequence engine
        """
        if not self.enabled:
            self.enabled = True
            self.load_button.setEnabled(True)
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(False)

    def reset(self):
        """
        Reset the sequence engine
        """
        # Started engine case
        if self.engine.is_started():
            msg = "Engine is still running \n"
            msg += "Use the STOP command (F7) \n"
            msg += "Then wait for it to terminate "
            QtGui.QMessageBox.warning(self, 'Engine still running',
                                      msg, QtGui.QMessageBox.Ok)
            return False
        # Loaded sequence case
        if self.engine.is_loaded():
            msg = "A sequence has been loaded \n"
            msg += "Quit anyway? "
            res = QtGui.QMessageBox.question(self, 'Sequence loaded', msg,
                                            QtGui.QMessageBox.Yes,
                                            QtGui.QMessageBox.Cancel)
            if res == QtGui.QMessageBox.Cancel:
                return False
            self.log('UNLOAD')
            self.engine.interrupt()
            # Set the buttons status
            self.load_button.setEnabled(True)
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(False)
        return True

    def load(self, file_path=None):
        """
        Load a file (with the file_path argument if given)
        """
        # Set path
        if file_path is not None:
            self.file_path = unicode(file_path)
        # Test file path
        if not self.file_path:
            self.log(u"NO FILE TO LOAD")
            return
        # Test if the file exists
        file_name = os.path.basename(self.file_path)
        if not os.path.isfile(self.file_path):
            self.log(u"FILE NOT FOUND : {}".format(file_name))
            return
        # Load the sequence
        self.log(u'LOAD : {}'.format(file_name))
        try :
            self.engine.load(self.file_path)
        except StandardError as error:
            self.log(u'ERROR : '+ unicode(error))
            return
        sequence_id = self.engine.sequence.xml_sequence.sequence_id
        self.log(u'SEQUENCE LOADED : {}'.format(sequence_id))
        # Set the buttons status
        self.load_button.setEnabled(False)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(True)

    def log(self, msg, end="\n"):
        """
        Method to log a message with an end character
        """
        self.log_signal.emit(unicode(msg), unicode(end))

    #### Sequence Engine Handling ####

    class EngineRunner(QtCore.QThread):
        """
        Thread to handle the sequence engine while it's running
        """
        def run(self):
            """
            Wait for the sequence execution to terminate
            """
            engine = self.parent().engine
            engine.start()
            engine.wait()

    class EngineLogger(QtCore.QThread):
        """
        Thread to print dots while the engine is running
        """
        def run(self):
            """
            Print dots every half of a second
            """
            tick = 1
            while self.parent().run_thread.isRunning():
                self.parent().log(".", end="")
                self.msleep(tick)
                print('hey!')

    #### Signals target ####

    def on_load(self):
        """
        Load the sequence in the Sequence Enginguest_teste
        """
        # Empty sequence or already started engine case
        if not self.enabled or self.engine.is_started():
            return
        # Require a file path
        if self.path_request_enabled:
            self.path_requested.emit()
            return
        # Load
        self.load()

    def on_run(self):
        """
        Execute the loaded sequence
        """
        if self.engine.is_loaded():
            # Set the buttons status
            self.load_button.setEnabled(False)
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            # Start the engine handler thread
            self.log("RUN")
            self.log(".", end="")
            self.execution_started.emit()
            self.run_thread = self.EngineRunner(self, finished=self.on_finished)
            self.run_thread.start()
            self.log_thread = self.EngineLogger(self)
            self.log_thread.start()

    def on_stop(self):
        """
        Send a stop signal to the engine
        """
        # Sequence not loaded case
        if not self.engine.is_loaded():
            return
        # Sequence started case : USER STOP
        if self.engine.is_started():
            self.log('.')
            self.log('USER STOP')
            self.engine.interrupt()
        # Sequence not started case : UNLOAD
        else:
            self.log('UNLOAD')
            self.engine.interrupt()
            # Set the buttons status
            self.load_button.setEnabled(True)
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(False)

    def on_finished(self):
        """
        Update the main widget since the execution is over
        """
        self.log_thread.wait()
        self.log('.')
        self.log('FINISHED')
        self.execution_finished.emit()
        # Set the buttons status
        self.load_button.setEnabled(True)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(False)

    #### Close Event ####

    def closeEvent(self, event):
        """
        Override closeEvent to handle secial cases
        """
        if not self.reset():
            event.ignore()


# Main execution
if __name__ == '__main__':
    # Imports to test the widget
    import sequence
    from sequence.core.engine import stream_sequence_logs
    # Create the widget
    stream_sequence_logs(sys.stdout)
    app = QtGui.QApplication(sys.argv)

    def print_in_console(msg, end):
        print(msg)

    ui = ControlWidget(log_signal=print_in_console)
    path = os.path.join(
        os.path.dirname(sequence.__file__), os.pardir,
        "examples", "BranchTest.xml")
    ui.set_path(path)
    ui.enable()
    ui.show()
    # Run the widget
    sys.exit(app.exec_())
