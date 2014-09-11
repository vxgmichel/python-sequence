# -*- coding: utf-8 -*-

""" Main module for the block sequence editor """

#-------------------------------------------------------------------------------
# Name:        BlockSequenceEditor
# Purpose:     Main module for the sequence diagram editor
#
# Author:      michel.vincent
#
# Created:     21/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------

import locale
import os, sys
from PyQt4 import QtGui, QtCore
from sequence.widget.editor.editor import EditorWidget



if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ui = EditorWidget()
    if len(sys.argv)>1 :
        filename = sys.argv[1].decode(locale.getpreferredencoding())
        ui.open(filename)
    ui.show()
    sys.exit(app.exec_())
