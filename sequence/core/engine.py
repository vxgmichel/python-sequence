# -*- coding: utf-8 -*-

""" Main module for sequence execution """

#-------------------------------------------------------------------------------
# Name:        SequenceEngine
# Purpose:     Load and execute sequences from xml files
#
# Author:      michel.vincent
#
# Created:     26/09/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Imports
import logging
from sequence.common.parser import parse_sequence_file
from sequence.common.constant import LOGGER
from sequence.core.runable import RootSequenceThread


# Sequence Engine
class SequenceEngine():
    """
    Main class of the sequence engine
    """
    is_loaded = lambda self: self.loaded
    is_started = lambda self: self.started
    is_interrupted = lambda self: self.interrupted

    def __init__(self):
        """
        Init method
        """
        self.sequence = None
        self.loaded = False
        self.started = False
        self.interrupted = False

    def load(self, xml_file, max_depth = None, backup = None):
        """
        Load an xml file

        :param xml_file: str -- path of the xml file to load
        :param max_depth: int -- maximum depth for sequence creation
        :param backup: str -- path of the xml backup file
        """
        if self.loaded and self.started:
            if not self.interrupted:
                return
            self.wait()
        xml_sequence = parse_sequence_file(xml_file, max_depth, backup)
        self.sequence = RootSequenceThread(xml_sequence)
        self.loaded = True
        self.started = False
        self.interrupted = False

    def start(self):
        """
        Start the sequence
        """
        if self.loaded and not self.started:
            self.sequence.start()
            self.started = True
            self.interrupted = False

    def wait(self, timeout=None):
        """
        Wait for the sequence to terminate
        Return False if the timeout is expired, True otherwise
        """
        if self.loaded and self.started:
            self.sequence.join(timeout)
            if self.sequence.is_alive():
                return False
            self.sequence = None
            self.interrupted = False
            self.started = False
            self.loaded = False
        return True

    def interrupt(self):
        """
        Interrupt the sequence execution
        """
        if self.loaded:
            if self.started:
                self.sequence.stop()
                self.interrupted = True
            else:
                self.sequence = None
                self.loaded = False



# Console logging
class SequenceLoggingFormatter(logging.Formatter):
    """
    A log formatter customized to handle sequence execution logs
    """
    def format(self, record):
        """
        Override the "format" method of the Formatter class
        """
        time = u'{:8},{:03}'
        time = time.format(self.formatTime(record, '%H:%M:%S'),
                           int(record.msecs))
        string = u'{} | {:5} | {:16} | {:11} | {:16} | {:7} |'
        string = string.format(time, record.thread, record.sequenceID,
                               record.type, record.ID, record.levelname)
        if record.msg :
            msg = record.msg
            if isinstance(msg, str):
                try:
                    msg = unicode(msg)
                except:
                    try:
                        msg = msg.decode('utf-8')
                    except:
                        msg = u"[Cannot display message : encoding error]"
            string += u' ' + u'{}'.format(msg)
        return string



# Set custom stream handler
def stream_sequence_logs(stream, debug_level=logging.INFO):
    """
    Add the custom stream handler to the execution logger
    """
    handler = logging.StreamHandler(stream)
    handler.setFormatter(SequenceLoggingFormatter())
    handler.setLevel(debug_level)
    LOGGER.addHandler(handler)

# Add an execution log handler
def add_log_handler(handler):
    """
    Add a log handler to the execution logger
    """
    LOGGER.addHandler(handler)

