# -*- coding: utf-8 -*-

""" Module for creating and handling the links between the blocks """

#-------------------------------------------------------------------------------
# Name:        Scene
# Purpose:     Module for creating and handling the links between the blocks
#
# Author:      michel.vincent
#
# Created:     21/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Imports
from PyQt4 import QtGui, QtCore


# Link Class Definition
class Link(QtGui.QGraphicsPolygonItem):
    """
    Class to create and handle the links between the blocks
    """

    def __init__(self, blocIO1, blocIO2, scene):
        """
        Initialize the link with two connectors and the drawing scene
        """
        super(Link, self).__init__(scene=scene)
        if blocIO1.is_input:
            self.start_block_io = blocIO2
            self.end_block_io = blocIO1
        else:
            self.start_block_io = blocIO1
            self.end_block_io = blocIO2
        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setZValue(-1)
        self.setAcceptHoverEvents(True)

    def setLine(self):
        """
        Create the line between the two connectors
        """
        # Get coordinates
        x1 = self.start_block_io.scenePos().x()
        x2 = self.end_block_io.scenePos().x()
        y1 = self.start_block_io.scenePos().y()
        y2 = self.end_block_io.scenePos().y()
        # Get blocks caracterictics
        yStartBloc = self.start_block_io.parentItem().scenePos().y()
        yEndBloc = self.end_block_io.parentItem().scenePos().y()
        blocSize = self.start_block_io.parentItem().size
        # Test if the block are on the same height
        onSameHeight = (yEndBloc + blocSize > yStartBloc and
                        yEndBloc < yStartBloc + blocSize)
        # Set margins and ratio
        deport = self.start_block_io.size*2+self.start_block_io.y()/4
        ratio = 2
        # Case 1 : 3 segments
        if (x2 - x1)/2 > deport or (x1 < x2 and onSameHeight):
            self.plist = [QtCore.QPointF(x1, y1),
                     QtCore.QPointF(x1 + (x2-x1)/ratio, y1),
                     QtCore.QPointF(x1 + (x2-x1)/ratio, y2),
                     QtCore.QPointF(x2, y2)]
        # Case 2 : 5 segments (not on the same height)
        elif not onSameHeight:
            self.plist = [QtCore.QPointF(x1, y1),
                     QtCore.QPointF(x1 + deport, y1),
                     QtCore.QPointF(x1 + deport, y1 + (y2-y1)/ratio),
                     QtCore.QPointF(x2 - deport, y1 + (y2-y1)/ratio),
                     QtCore.QPointF(x2 - deport, y2),
                     QtCore.QPointF(x2, y2)]
        # Case 3 : 5 segments (on the same height)
        else:
            if y1 < y2:
                self.plist = [QtCore.QPointF(x1, y1),
                         QtCore.QPointF(x1 + deport, y1),
                         QtCore.QPointF(x1 + deport,
                                        max(yEndBloc,
                                            yStartBloc) + blocSize + deport),
                         QtCore.QPointF(x2-deport,
                                        max(yEndBloc,
                                            yStartBloc) + blocSize + deport),
                         QtCore.QPointF(x2-deport, y2),
                         QtCore.QPointF(x2, y2)]
            else:
                self.plist = [QtCore.QPointF(x1, y1),
                         QtCore.QPointF(x1 + deport, y1),
                         QtCore.QPointF(x1 + deport,
                                        min(yEndBloc, yStartBloc) - deport),
                         QtCore.QPointF(x2-(deport),
                                        min(yEndBloc, yStartBloc) - deport),
                         QtCore.QPointF(x2-(deport), y2),
                         QtCore.QPointF(x2, y2)]
        self.setPolygon(QtGui.QPolygonF(self.plist))

    def disconnectIO(self):
        """
        Diconnect the two connectors
        """
        self.start_block_io.disconnect_from(self.end_block_io)

    def hoverEnterEvent(self,event):
        """
        Change the cursor when the link is hovered
        """
        self.setCursor(QtCore.Qt.PointingHandCursor)
        super(Link, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self,event):
        """
        Restore the cursor
        """
        self.setCursor(QtCore.Qt.ArrowCursor)
        super(Link, self).hoverLeaveEvent(event)

    def shape(self):
        """
        Overrided shape method
        """
        path = QtGui.QPainterPath()
        path.moveTo(self.plist[0])
        for point in self.plist[1:]+ self.plist[-2::-1]:
            path.lineTo(point)
        stroker = QtGui.QPainterPathStroker()
        stroker.setWidth(6)
        path = stroker.createStroke(path)
        return path

    def boundingRect(self):
        """
        Overrided boundingRect method
        """
        rect = super(Link, self).boundingRect()
        margin =  3
        return QtCore.QRectF(rect.x()-margin, rect.y()-margin,
                             rect.width()+2*margin,
                             rect.height()+2*margin)

    def paint(self, painter, option, widget):
        """
        Overrided paint method
        """
        if self.isSelected():
            painter.setPen(QtGui.QPen(QtCore.Qt.black, 1.5,
                                      QtCore.Qt.DashLine))
        else:
            painter.setPen(QtGui.QPen(QtCore.Qt.black, 1.5,
                                      QtCore.Qt.SolidLine))
        painter.drawPolyline(self.polygon())
