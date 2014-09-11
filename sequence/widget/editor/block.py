# -*- coding: utf-8 -*-

""" Module for creating and managing blocks """

#-------------------------------------------------------------------------------
# Name:        BlockSequenceEditor
# Purpose:     Module for creating and managing blocks
#
# Author:      michel.vincent
#
# Created:     21/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Imports
import os
from copy import deepcopy
from PyQt4 import QtGui, QtCore


# Imports from packages
from sequence.widget.editor.blockio import BlockIO
from sequence.common.constant import XBM, BES, IMAGES_DIR


# Color Definition
COLORDICT = {BES.NP:QtGui.QColor(220,220,230,180),
             BES.OK:QtGui.QColor(150,220,150,180),
             BES.KO:QtGui.QColor(220,150,150,180),
             BES.BG:QtGui.QColor(150,150,220,180)}


# Block Class Definition
class Block(QtGui.QGraphicsRectItem):
    """
    Class reprensenting a block in the drawing area
    """
    max_width = 100
    max_height = 100
    width = 80
    height = 80
    size = max(max_height, max_width)
    magnetism = 10

    class CustomText(QtGui.QGraphicsTextItem):
        """
        Custom text item to rename a block directly on the drawing area
        """
        def __init__(self, parent):
            QtGui.QGraphicsTextItem.__init__(self, parent)
            self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
            self.first_click = False

        def keyPressEvent(self, event):
            """
            Handle the 'return' and 'enter' keys
            """
            if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
                self.clearFocus()
                return
            QtGui.QGraphicsTextItem.keyPressEvent(self, event)

        def focusInEvent(self, event):
            """
            Detect the first click
            """
            self.first_click = True
            QtGui.QGraphicsTextItem.focusInEvent(self, event)

        def mousePressEvent(self, event):
            """
            Select the whole text on the first click
            """
            QtGui.QGraphicsTextItem.mousePressEvent(self, event)
            if self.first_click:
                self.first_click = False
                cursor = QtGui.QTextCursor(self.document())
                cursor.select(QtGui.QTextCursor.LineUnderCursor)
                self.setTextCursor(cursor)

        def mouseDoubleClickEvent(self, event):
            """
            Select the whole text on double click
            """
            QtGui.QGraphicsTextItem.mouseDoubleClickEvent(self, event)
            cursor = QtGui.QTextCursor(self.document())
            cursor.select(QtGui.QTextCursor.LineUnderCursor)
            self.setTextCursor(cursor)

        def focusOutEvent(self, event):
            """
            Handle the user input when he is done
            """
            new_id = unicode(self.toPlainText()).strip()
            if new_id != u"":
                self.parentItem().xml_block.block_id = new_id
                self.parentItem().scene().editor.set_changed(True)
            self.parentItem().update()
            self.parentItem().setSelected(True)
            QtGui.QGraphicsTextItem.focusOutEvent(self, event)

        def hoverMoveEvent(self, event):
            """
            Change cursor to indicate the item is editable
            """
            QtGui.QGraphicsTextItem.hoverMoveEvent(self, event)
            self.setCursor(QtCore.Qt.IBeamCursor)


    def __init__(self, scene, xml_block):
        """
        Initialize the block whith the scene and its xml representation
        """
        super(Block, self).__init__(scene=scene)  # ajout automatique dans la scene

        # Manage XML model
        self.xml_block = xml_block
        if self.xml_block not in self.scene().sequence_item.sequence.blocks:
            self.scene().sequence_item.sequence.blocks.append(self.xml_block)
            self.scene().editor.set_changed(True)

        # Initialisation graphique
        self.setRect(0, 0, self.width, self.height)
        self.color = COLORDICT[BES.NP]
        self.setBrush(QtGui.QBrush(self.color))
        self.graphictext = self.CustomText(self)
        self.graphictext.setPos(self.rect().bottomLeft())
        self.setFlags(QtGui.QGraphicsItem.ItemIsMovable|
                      QtGui.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.add_image()

        # Update with model
        self.update()

        # Create IO
        self.input_item = None
        self.output_item = None
        if self.xml_block.inputs is not None:
            self.input_item = BlockIO(self, is_input=True)
        if self.xml_block.outputs is not None:
            self.output_item = BlockIO(self, is_input=False)

    def update(self):
        """
        Update the block graphics
        """
        # Update coordinates
        self.setX(int(self.xml_block.extra['X'])-self.width//2)
        self.setY(int(self.xml_block.extra['Y'])-self.height//2)
        self.update_coordinates(final=True)
        # Update name
        new_id = self.valid_block_id(self.xml_block.block_id)
        if new_id != self.xml_block.block_id:
            self.xml_block.block_id = new_id
            self.scene().editor.set_changed(True)
        self.graphictext.setPlainText(self.xml_block.block_id)
        return super(Block,self).update()

    def valid_block_id(self, block_id):
        """
        Find the next valid name for the block
        """
        id_list = [block.xml_block.block_id
                   for block in self.scene().block_list
                   if block is not self]
        if block_id not in id_list:
            return block_id
        # Looking for a valid name
        nb = 2
        if block_id.split()[-1].isdigit():
            nb = int(block_id.split()[-1])+1
            block_id = ' '.join(block_id.split()[:-1])
        current = block_id+' '+str(nb)
        while current in id_list:
            nb += 1
            current = block_id+' '+str(nb)
        return current

    def has_same_id(self, block):
        """
        Compare ids with another block
        """
        if not block:
            return False
        return self.xml_block.block_id == block.xml_block.block_id

    def add_image(self):
        """
        Add the corresponding image to the block
        """
        if self.xml_block.block_type == XBM.ACTION:
            module = self.xml_block.properties.module
            module_to_name = self.scene().editor.module_to_name
            name = module_to_name.get(module, 'Undefined')
        else:
            name = self.xml_block.block_type
        url = os.path.join(IMAGES_DIR, name)
        image = QtGui.QPixmap(url)
        if image.isNull():
            url = os.path.join(IMAGES_DIR, 'Undefined')
            image = QtGui.QPixmap(url)
        image = image.scaled(self.rect().width()-10,
                             self.rect().height()-10,
                             QtCore.Qt.KeepAspectRatio,
                             QtCore.Qt.SmoothTransformation)
        self.image = QtGui.QGraphicsPixmapItem(image, self)
        self.image.setPos(5, 5)
        self.image.setZValue(-6)

    def delete(self):
        """
        Delete the block
        """
        self.remove_links()
        self.scene().editor.block_model.update(None)
        self.scene().sequence_item.sequence.remove_block(self.xml_block)
        self.scene().editor.set_changed(True)
        self.scene().block_list.remove(self)
        self.scene().removeItem(self)

    def draw_lines(self):
        """
        Update block connections
        """
        for item in self.childItems():
            if isinstance(item, BlockIO):
                item.connect_all()

    def remove_links(self):
        """
        Remove all connections of the block
        """
        for item in self.childItems():
            if isinstance(item, BlockIO):
                item.disconnect_all()


    def paint(self, painter, option, widget):
        """
        Overrided paint method
        """
        if self.isSelected():
            painter.setPen(QtGui.QPen(QtCore.Qt.black, 1.5, QtCore.Qt.DashLine))
            painter.setBrush(QtGui.QBrush(self.color.darker(115)))
        else:
            painter.setPen(QtGui.QPen(QtCore.Qt.black, 1.5))
            painter.setBrush(self.brush())
        painter.drawRoundedRect(self.rect(), 5, 5)

    def set_execution_state(self, state):
        """
        Set block color according to its execution state
        """
        self.color = COLORDICT.get(state, COLORDICT[BES.NP])
        self.setBrush(QtGui.QBrush(self.color))

    def mouseMoveEvent(self, event):
        """
        Update block graphics when it is moving
        """
        super(Block, self).mouseMoveEvent(event)
        event.accept()
        for block in self.scene().selectedItems():
            if isinstance(block, Block):
                block.update_coordinates()
            for item in block.childItems():
                if isinstance(item, BlockIO):
                    for link in item.links.values():
                        link.setLine()
        self.scene().selectionChanged.emit()


    def update_coordinates(self, final=False):
        """
        Update block coordinates considering magnetism, limits and collisions
        """
        # Magnetic coordinates
        closest_x = closest_y = None
        list_x = [block for block in self.scene().block_list
                  if block != self and abs(self.x()-block.x())<self.magnetism]
        list_y = [block for block in self.scene().block_list
                  if block != self and abs(self.y()-block.y())<self.magnetism]
        if list_x:
            closest_x = min(list_x, key=lambda block:abs(self.y()-block.y()))
        if list_y:
            closest_y = min(list_y, key=lambda block:abs(self.x()-block.x()))
        if closest_x:
            self.setX(closest_x.x())
        if closest_y:
            self.setY(closest_y.y())
        # Handle collision
        if final:
            while any(self != block and block.pos() == self.pos()
                      for block in self.scene().block_list):
                self.setX(self.x()+2*self.magnetism)
                self.setY(self.y()+2*self.magnetism)
        # Foreground Limit detection
        width = self.scene().sceneRect().width()
        height = self.scene().sceneRect().height()
        if self.x()+self.width//2-self.max_width//2 < 0:
            self.setX(self.max_width//2-self.width//2)
        elif self.x()+self.width//2+self.max_width//2 >= width:
            self.setX(width-self.max_width//2-self.width//2)
        if self.y()+self.height//2-self.max_height//2 < 0:
            self.setY(self.max_height//2-self.height//2)
        elif self.y()+self.height//2+self.max_height//2 >= height:
            self.setY(height-self.max_height//2-self.height//2)
        # Set data
        if final:
            old_pos = self.xml_block.extra['X'], self.xml_block.extra['Y']
            self.xml_block.extra['X'] = str(int(self.x())+self.width//2)
            self.xml_block.extra['Y'] = str(int(self.y())+self.height//2)
            new_pos = self.xml_block.extra['X'], self.xml_block.extra['Y']
            if old_pos != new_pos:
                self.scene().editor.set_changed(True)
        # Update link
        for item in self.childItems():
            if isinstance(item, BlockIO):
                for link in item.links.itervalues():
                    link.setLine()


    def setSelected(self, boolean):
        """
        Update property editor when the block is selected
        """
        super(Block, self).setSelected(boolean)
        if boolean:
            self.scene().editor.block_model.update(self)

    def hoverMoveEvent(self, event):
        """
        Set an open-hand cursor and make the block darker
        """
        super(Block, self).hoverMoveEvent(event)
        self.setCursor(QtCore.Qt.OpenHandCursor)
        self.setBrush(QtGui.QBrush(self.color.darker(110)))


    def hoverLeaveEvent(self, event):
        """
        Restore regular cursor and color
        """
        super(Block, self).hoverLeaveEvent(event)
        self.setCursor(QtCore.Qt.ArrowCursor)
        self.setBrush(QtGui.QBrush(self.color))

    def mousePressEvent(self, event):
        """
        Set a closed hand cursor
        """
        super(Block, self).mousePressEvent(event)
        self.setCursor(QtCore.Qt.ClosedHandCursor)


    def mouseReleaseEvent(self, event):
        """
        Update block after it has been moved
        """
        super(Block, self).mouseReleaseEvent(event)
        for block in self.scene().selectedItems():
            if isinstance(block, Block):
                block.update_coordinates(final=True)
        if self in self.scene().selectedItems():
            self.scene().editor.block_model.update(self)
        self.setCursor(QtCore.Qt.OpenHandCursor)


