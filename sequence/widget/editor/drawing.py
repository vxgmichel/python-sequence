# -*- coding: utf-8 -*-

""" Module for creating and handling the drawing scene """

#-------------------------------------------------------------------------------
# Name:        Scene
# Purpose:     Module for creating and handling the drawing scene
#
# Author:      michel.vincent
#
# Created:     21/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Imports
import os
from PyQt4 import QtGui, QtCore


# Imports from packages
from sequence.common.constant import XBM, BES
from sequence.common.parser import XMLBlock
from sequence.widget.editor.block import Block
from sequence.widget.editor.blockio import BlockIO
from sequence.widget.editor.link import Link


# Scene class definition
class DrawingScene(QtGui.QGraphicsScene):

    def __init__(self, parent, sequence_item):
        """
        Initialize the drawing scene with the drawing area and the sequence
        """
        super(DrawingScene, self).__init__(parent)
        self.sequence_item = sequence_item
        self.editor = sequence_item.editor
        self.scale = 1
        self.select_rect = None
        self.foreground = None
        self.block_list = []
        self.setSceneRect(0, 0, 2000, 1400)
        self.setBackgroundBrush(QtCore.Qt.gray)

    def clear(self, total=True):
        """
        Clear the drawing scene
        """
        self.block_list = []
        super(DrawingScene, self).clear()
        self.foreground = QtGui.QGraphicsRectItem(self.sceneRect())
        self.foreground.setBrush(QtCore.Qt.white)
        self.foreground.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        self.foreground.setZValue(-2)
        self.addItem(self.foreground)
        if total:
            self.parent().centerOn(0,0)
        item = self.editor.get_current_sequence_item()
        if total and item and item.scene is self:
            self.editor.block_model.update(None)

    def dragMoveEvent(self, event):
        """
        Overrided dragMoveEvent method
        """
        event.accept()

    def dropEvent(self, event):
        """
        Create a new block when it is dropped from the block list
        """
        center = event.scenePos()
        if center not in self.sceneRect():
            return
        try:
            item = event.source().currentItem()
        except:
            return
        if event.source() is self.editor.ui.block_list:
            name = unicode(item.text(0))
            family = unicode(item.parent().text(0))
            data = self.editor.block_mapping[family][name]
            if isinstance(data, tuple):
                data, module = data
            xml_block = XMLBlock(name, data)
        elif event.source() is self.editor.ui.subsequence_editor:
            if self.sequence_item is not item.parent():
                return
            name = item.sequence.sequence_id
            data = XBM.MACRO
            xml_block = XMLBlock(name, data)
            xml_block.properties.sequence_id = name
        else:
            return
        if data == XBM.ACTION: 
            xml_block.properties.module = module
            xml_block.create_action()
        xml_block.extra['X'] = unicode(int(center.x()))
        xml_block.extra['Y'] = unicode(int(center.y()))
        block = Block(self, xml_block)
        self.block_list.append(block)
        self.clearSelection()
        block.setSelected(True)
        self.parent().setFocus()

    def update(self, total=True):
        """
        Update the drawing area
        """
        self.clear(total)
        for block in self.sequence_item.sequence.blocks:
            self.block_list.append(Block(self, block))
        for block in self.block_list:
            block.draw_lines()
        item = self.editor.get_current_sequence_item()
        if item and item.scene is self:
            try:
                model_block = self.editor.block_model.block
                current = next(block for block in self.block_list
                                if block.has_same_id(model_block))
                self.editor.block_model.update(current)
            except StopIteration:
                self.editor.block_model.update(None)
        self.clearSelection()
        super(DrawingScene, self).update()

    def update_block_model(self):
        """
        Update model block for the property editor
        """
        for item in self.selectedItems():
            if isinstance(item, Block):
                self.editor.block_model.update(item)
                return
        self.editor.block_model.update(None) 

    def keyPressEvent(self,event):
        """
        Delete selected blocks when the delete key is pressed
        """
        super(DrawingScene, self).keyPressEvent(event)
        if event.matches(QtGui.QKeySequence.Delete) and \
           not isinstance(self.focusItem(), Block.CustomText):
            # Suppression des liens sélectionnés
            for item in self.selectedItems():
                if isinstance(item, Link):
                    item.disconnectIO()
                    self.removeItem(item)
            # Suppression des blocs sélectionnés
            for item in self.selectedItems():
                if isinstance(item, Block):
                    item.delete()

    def mousePressEvent(self, event):
        """
        Update selection rectangle when the left button is pressed
        """
        super(DrawingScene, self).mousePressEvent(event)
        # Ignore when the event doesn't come from left mouse button
        if event.button() != QtCore.Qt.LeftButton:
            return
        if self.itemAt(event.scenePos()) in [None, self.foreground]:
            self.select_rect = QtGui.QGraphicsRectItem(scene = self)
            self.select_rect.setPen(QtGui.QPen(QtCore.Qt.DotLine))
            self.select_rect.setPos(event.scenePos())

    def mouseMoveEvent(self, event):
        """
        Update selection rectangle when the mouse is moving
        """
        super(DrawingScene, self).mouseMoveEvent(event)
        if self.select_rect is not None:
            width = event.scenePos().x()-self.select_rect.x()
            height = event.scenePos().y()-self.select_rect.y()
            rect = QtCore.QRectF(0, 0, width, height).normalized()
            self.select_rect.setRect(rect)

    def mouseReleaseEvent(self, event):
        """
        Update selection rectangle when the left button is released
        """
        super(DrawingScene, self).mouseReleaseEvent(event)
        # Ignore when the event doesn't come from left mouse button
        if event.button() != QtCore.Qt.LeftButton:
            return
        if self.select_rect is not None:
            for item in self.items():
                if self.select_rect.collidesWithItem(item):
                    item.setSelected(True)
            self.removeItem(self.select_rect)
            self.select_rect = None

    def wheelEvent(self, event):
        """
        Handle the zoom mecanism when the wheel is used
        """
        if event.modifiers() == QtCore.Qt.ControlModifier:
            value = self.editor.ui.zoom_slider.value()
            if(event.delta() < 0 ):
                value *= 0.9
                if value < 10:
                    value = 10
            if(event.delta() > 0 ):
                value *= 1.1
                if value > 400:
                    value = 400
            self.editor.ui.zoom_slider.setValue(int(value))
            event.accept()    
            
    def reset_execution_state(self):
        """
        Reset blocks' execution state (reset color)
        """
        for block in self.block_list:
            block.set_execution_state(BES.NP)
