# -*- coding: utf-8 -*-

""" Module for the Input/output block pins """

#-------------------------------------------------------------------------------
# Name:        BlockIO
# Purpose:     Module for the Input/output block pins
#
# Author:      michel.vincent
#
# Created:     21/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Imports
from PyQt4 import QtGui, QtCore
from sequence.widget.editor.link import Link


# BlockIO Class Definition
class BlockIO(QtGui.QGraphicsEllipseItem):
    """
    Class representing a block connector
    """
    size = 10

    def __init__(self, parent, is_input):
        """
        Initialize with parent and direction
        """
        # Init parent
        super(BlockIO, self).__init__(parent)
        self.xml_block = parent.xml_block
        # IO informations
        self.is_input = is_input
        if is_input:
            self.is_multiple = self.xml_block.handle_multiple_inputs()
            self.xml_blocks = parent.xml_block.inputs
        else:
            self.is_multiple = self.xml_block.handle_multiple_outputs()
            self.xml_blocks = parent.xml_block.outputs
        # Init links
        self.links = {}
        # Graphic configuration
        if self.is_input:
            self.setX(0)
            self.setY(parent.height//2)
            self.setBrush(QtGui.QBrush(QtGui.QColor("red")))
        else:
            self.setX(parent.width)
            self.setY(parent.height//2)
            self.setBrush(QtGui.QBrush(QtGui.QColor("green")))
        self.update_rectangle()
        self.setFlags(QtGui.QGraphicsItem.ItemIgnoresParentOpacity|
                      QtGui.QGraphicsItem.ItemDoesntPropagateOpacityToChildren)
        self.setAcceptHoverEvents(True)

    def update_rectangle(self, ratio=1):
        """
        Update rectangle using a given ratio
        """
        nb_links = len(self.links)
        width = self.size*ratio
        height = min(max(nb_links,1),3)*self.size*ratio
        self.setRect(-width//2, -height//2, width, height)

    def boundingRect(self):
        """
        Overrided boundingRect method
        """
        width = self.rect().width()*2
        height = self.rect().height()+self.size
        return QtCore.QRectF(-width//2, -height//2, width, height)

    def shape(self):
        """
        Overrided shape method
        """
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, option, widget):
        """
        Overrided paint method
        """
        cx = -self.rect().width()//2+2
        cy = -self.rect().height()//2+2
        gradient = QtGui.QRadialGradient(cx, cy, 8)
        if self.is_input:
            gradient.setColorAt(0, QtCore.Qt.white)
            gradient.setColorAt(1, QtCore.Qt.red)
        else:
            gradient.setColorAt(0, QtCore.Qt.white)
            gradient.setColorAt(1, QtCore.Qt.darkGreen)
        painter.setBrush(QtGui.QBrush(gradient))
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        if self.is_multiple:
            painter.drawRect(self.rect())
        else:
            painter.drawEllipse(self.rect())

    def connect_with(self, io_block):
        """
        Connect the pin with a given pin
        """
        # Update graphics
        if io_block not in self.links:
            link = Link(self, io_block, scene=self.scene())
            self.links[io_block] = link
            io_block.links[self] = link
            self.update_rectangle()
            io_block.update_rectangle()
            link.setLine()
        # Update data
        if io_block.xml_block not in self.xml_blocks:
            self.xml_blocks.append(io_block.xml_block)
        if self.xml_block not in io_block.xml_blocks:
            io_block.xml_blocks.append(self.xml_block)
        # Set as modified
        self.scene().editor.set_changed(True)

    def disconnect_from(self, io_block):
        """
        Disconnect the pin from a given pin
        """
        # Update graphics
        self.scene().removeItem(self.links[io_block])
        self.links.pop(io_block)
        io_block.links.pop(self)
        # Update data
        self.xml_blocks.remove(io_block.xml_block)
        io_block.xml_blocks.remove(self.xml_block)
        # Update rectangle
        self.update_rectangle()
        io_block.update_rectangle()
        # Set as modified
        self.scene().editor.set_changed(True)

    def connect_all(self):
        """
        Connect with all blocks in self.xml_blocks
        """
        for xml_block in self.xml_blocks:
            for item in self.scene().items():
                if isinstance(item, BlockIO) and item.xml_block is xml_block \
                   and item.is_input != self.is_input:
                    self.connect_with(item)

    def disconnect_all(self):
        """
        Disconnect from all the pins in self.links
        """
        for io_block in self.links.keys():
            self.disconnect_from(io_block)

    def hoverEnterEvent(self,event):
        """
        Change cursor when hovered
        """
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def hoverLeaveEvent(self,event):
        """
        Restore cursor
        """
        self.setCursor(QtCore.Qt.ArrowCursor)

    def mouseMoveEvent(self, event):
        """
        Handle the user movement while he's drawing a link
        """
        # Update valid rectangles
        for block in self.scene().block_list:
            for item in block.childItems():
                if isinstance(item, BlockIO) and \
                   self.parentItem() is not item.parentItem() and \
                   self.is_input != item.is_input :
                    item.update_rectangle(ratio=1.2)
        # Update the line
        self.tempLine.setLine(self.scenePos().x(), self.scenePos().y(),
                              event.scenePos().x(), event.scenePos().y())
        # Get hovered item
        hovered = self.scene().itemAt(event.scenePos())
        if isinstance(hovered, QtGui.QGraphicsPixmapItem):
            hovered = hovered.parentItem()
        boolean = False
        # Test hovered item
        if isinstance(hovered, BlockIO):
            boolean = hovered.is_input != self.is_input
            boolean = boolean and hovered.parentItem() is not self.parentItem()
        if isinstance(hovered, type(self.parentItem())):
            input_bool = self.is_input and hovered.output_item and \
                         (hovered.output_item.is_multiple or
                          hovered.output_item.links == {})
            output_bool = not self.is_input and hovered.input_item and\
                          (hovered.input_item.is_multiple or
                           hovered.input_item.links == {})
            boolean = input_bool or output_bool
        # Update the line
        if boolean:
            pen = QtGui.QPen(QtGui.QBrush(QtGui.QColor("Green")),2,
                             QtCore.Qt.SolidLine)
        else:
            pen = QtGui.QPen(QtGui.QBrush(QtGui.QColor("Red")), 2,
                             QtCore.Qt.DotLine)
        self.tempLine.setPen(pen)

    def mousePressEvent(self, event):
        """
        Create the line between the connector and the mouse
        """
        # Ignore when the event doesn't come from left mouse button
        if event.button() != QtCore.Qt.LeftButton:
            return
        # Create the line
        self.tempLine = QtGui.QGraphicsLineItem(scene=self.scene())
        self.tempLine.setZValue(-1)

    def mouseReleaseEvent (self, event):
        """
        Handle the connection after the user released the mouse button
        """
        # Ignore when the event doesn't come from left mouse button
        if event.button() != QtCore.Qt.LeftButton:
            return
        # Get hovered item
        hovered = self.scene().itemAt(event.scenePos())
        if isinstance(hovered, QtGui.QGraphicsPixmapItem):
            hovered = hovered.parentItem()
        # BlockIO type case
        if isinstance(hovered, BlockIO) \
           and self.is_input != hovered.is_input:
            if not self.is_multiple and self.links != {} :
                self.disconnect_from(next(self.links.iterkeys()))
            if not hovered.is_multiple and hovered.links != {}:
                hovered.disconnect_from(hovered.links.keys()[0])
            self.connect_with(hovered)
        # Block type case
        if isinstance(hovered, type(self.parentItem())) :
            if self.is_input and hovered.output_item and \
               (hovered.output_item.is_multiple or
                hovered.output_item.links == {}):
                if not self.is_multiple and self.links != {} :
                    self.disconnect_from(next(self.links.iterkeys()))
                self.connect_with(hovered.output_item)
            elif not self.is_input and hovered.input_item and\
                 (hovered.input_item.is_multiple or
                  hovered.input_item.links == {}):
                if not self.is_multiple and self.links != {} :
                    self.disconnect_from(next(self.links.iterkeys()))
                self.connect_with(hovered.input_item)
        # Update scene
        self.scene().selectionChanged.emit()
        self.scene().removeItem(self.tempLine)
        self.tempLine = None
        for item in self.scene().items():
            item.setOpacity(1)
            if isinstance(item, BlockIO):
                item.update_rectangle()
