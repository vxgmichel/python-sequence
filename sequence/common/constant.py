# -*- coding: utf-8 -*-

""" Module containing constants """

#-------------------------------------------------------------------------------
# Name:        Constants
# Purpose:     This module contains useful constants
#
# Author:      michel.vincent
#
# Created:     09/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Logger
import logging
LOGGER = logging.getLogger('SequenceExecution')
LOGGER.setLevel(logging.DEBUG)


# Directories
import os
from sequence.resource import images
IMAGES_DIR = os.path.dirname(images.__file__)


# Enum definition
def enum(**enums):
    """
    Function allowing the definition of enumerations

    :param enums: set of elements to enumerate
    :return: an enumeration
    """
    return type('Enum', (), enums)


# XML SEQUENCE MARKUPS:
XSM = enum(SEQUENCE = 'Sequence',
           BLOCKS = 'Blocks',
           SUBSEQUENCES = 'Subsequences',
           BACKUP = 'Backup',
           INPUTOUTPUT = 'InputOutput',
           PROPERTIES = 'Properties',
           PARAMETERS = 'Parameters',
           EXTRA = 'Extra')


# XML BLOCK MARKUPS:
XBM = enum(BEGIN = 'Begin',
           END = 'End',
           ACTION = 'Action',
           MACRO = 'Macro',
           BRANCH = 'Branch',
           TIMEINIT = 'TimeInit',
           WAIT = 'Wait')


# XML SEQUENCE ATTRIBUTES:
XSA = enum(SEQUENCEID = 'SequenceID',
           ID = 'ID',
           INPUT = 'Input',
           OUTPUT = 'Output',
           MODULE = 'Module',
           ITERATION = 'Iteration',
           TICK = 'Tick',
           TIME = 'Time',
           ABSOLUTE = 'Absolute')

# BLOCK EXECUTION STATE:
BES = enum(OK = 'OK',
           KO = 'KO',
           BG = 'BG',  # BeGin
           NP = 'NP',) # Not Passed
