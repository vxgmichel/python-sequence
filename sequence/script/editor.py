# -*- coding: utf-8 -*-

""" Main module for the block sequence editor """

# ------------------------------------------------------------------------------
# Name:        BlockSequenceEditor
# Purpose:     Main module for the sequence diagram editor
#
# Author:      michel.vincent
#
# Created:     21/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
# ------------------------------------------------------------------------------


import sys
import locale
from PyQt4 import QtGui
from sequence.widget.editor.editor import EditorWidget


def main(filename=None):
    if filename is None and len(sys.argv) > 1:
        filename = sys.argv[1].decode(locale.getpreferredencoding())
    app = QtGui.QApplication(sys.argv)
    ui = EditorWidget()
    if filename:
        ui.open(filename)
    ui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
