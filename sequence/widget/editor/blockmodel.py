# -*- coding: utf-8 -*-

""" Module to handle the block properties in the property editor """

#-------------------------------------------------------------------------------
# Name:        BlockModel
# Purpose:     Module to handle the block properties in the property editor
#
# Author:      michel.vincent
#
# Created:     30/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Imports
from PyQt4 import QtCore, QtGui
from collections import OrderedDict as ODict
from sequence.common.constant import XSM, XSA
from sequence.action.abstract import BaseEnum
from sequence.common.parser import BlockProperties


# BlockMOdel Class Definition
class BlockModel(QtGui.QStandardItemModel):
    """ Model of the XML block properties """

    # Signal emitted when the model is changed
    model_changed = QtCore.pyqtSignal()

    class PropertyItem(QtGui.QStandardItem):
        """ Inner class to represent a property """
        def __init__(self, v, key):
            self.datatype = type(v)
            self.is_sequence_id = (key == XSA.SEQUENCEID)
            QtGui.QStandardItem.__init__(self, unicode(v))

    def __init__ (self, editor, block=None, parent=None):
        """
        Initialize the model with the editor, the block and the QTreeView
        """
        super(BlockModel, self).__init__(parent)
        parent.setItemDelegate(CustomDelegate())
        self.editor = editor
        self.data_dict = {}
        self.block = block
        self.update(block)
        self.setColumnCount(2)

    def update(self, block=None, update_view=True):
        """
        Update the model with a block
        """
        # XMLBLock presence
        self.block = block
        if self.block is None:
             self.data_dict = {}
        else :
            xml_block = self.block.xml_block
            # Set data_dict
            self.data_dict = {"BlockID" : {XSA.ID : xml_block.block_id}}
            if xml_block.properties:
                prop_dict = xml_block.properties.get_dictionnary()
                self.data_dict[XSM.PROPERTIES] = prop_dict
            if xml_block.parameters != {}:
                self.data_dict[XSM.PARAMETERS] = ODict(xml_block.parameters)
            if xml_block.extra != {}:
                self.data_dict[XSM.EXTRA] = {}
                for name, value in xml_block.extra.iteritems():
                    if name in ['X','Y']:
                        self.data_dict[XSM.EXTRA][name] = int(value)
                    else:
                        self.data_dict[XSM.EXTRA][name] = value
        if update_view:
            # Update Tree
            self.clear()
            self.setColumnCount(2)
            parentItem = self.invisibleRootItem()
            for topkey in self.data_dict:
                topLevelItem = QtGui.QStandardItem(topkey)
                for k, v in self.data_dict[topkey].items():
                    key = QtGui.QStandardItem(k)
                    value = self.PropertyItem(v, k)
                    topLevelItem.appendRow([key, value])
                parentItem.appendRow(topLevelItem)
            # Update View
            self.parent().expandAll()
            self.parent().setIndentation(0)

    def apply(self):
        """
        Apply the model data to the block and update the graphics
        """
        # No data to apply case
        if self.block is None or  self.data_dict == {}:
            return
        # Get xml blokc
        xml_block = self.block.xml_block
        changed = False
        # Apply block ID
        if xml_block.block_id != self.data_dict["BlockID"][XSA.ID]:
            xml_block.block_id = self.data_dict["BlockID"][XSA.ID]
            changed = True
        # Apply properties
        if self.data_dict.get(XSM.PROPERTIES,{}):
            prop_dict = self.data_dict[XSM.PROPERTIES]
            if xml_block.properties.set_dictionary(prop_dict):
                changed = True
        # Apply parameters
        if self.data_dict.get(XSM.PARAMETERS,{}) and \
           xml_block.parameters != self.data_dict[XSM.PARAMETERS]:
            xml_block.parameters = self.data_dict[XSM.PARAMETERS]
            changed = True
        # Apply extras
        if self.data_dict.get(XSM.EXTRA,{}):
            for name, value in self.data_dict[XSM.EXTRA].iteritems():
                if xml_block.extra[name] != unicode(value):
                    xml_block.extra[name] = unicode(value)
                    changed = True
        # Emit changed signal
        if changed:
            self.model_changed.emit()
            self.block.update()

    def flags(self, index):
        """
        Overrided flags method
        """
        item = self.itemFromIndex(index)
        col = index.column()
        if isinstance(item, self.PropertyItem) and item.datatype == bool:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable
        if col == 0 or not index.parent().isValid():
            return QtCore.Qt.ItemIsEnabled
        return super(BlockModel, self).flags(index)

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                return "Property"
            elif section == 1:
                return "Value"
        else:
            return super(BlockModel, self).headerData(section, orientation, role)

    def data(self, index, role):
        """
        Overrided data method
        """
        row = index.row()
        col = index.column()
        item = self.itemFromIndex(index)
        if isinstance(item, self.PropertyItem) and item.datatype == int:
            if role == QtCore.Qt.EditRole:
                return self.data(index, QtCore.Qt.DisplayRole).toInt()[0]
        if isinstance(item, self.PropertyItem) and item.datatype == bool:
            if role == QtCore.Qt.DisplayRole:
                return QtCore.QVariant()
            if role == QtCore.Qt.CheckStateRole:
                if self.data(index, QtCore.Qt.EditRole).toBool():
                    return QtCore.Qt.Checked
                return QtCore.Qt.Unchecked
        if isinstance(item, self.PropertyItem) and item.datatype == float:
            if role == QtCore.Qt.EditRole:
                return self.data(index, QtCore.Qt.DisplayRole).toDouble()[0]
        if not index.parent().isValid():
            if role ==  QtCore.Qt.BackgroundRole:
                return QtGui.QColor(120,120,120)
            if role ==  QtCore.Qt.ForegroundRole:
                return QtGui.QColor("white")
            if role ==  QtCore.Qt.FontRole:
                font = QtGui.QFont()
                font.setBold(True)
                return font
        elif (role == QtCore.Qt.BackgroundRole or
           (role == QtCore.Qt.DecorationRole and col==0)):
            parentRow = index.parent().row()
            if parentRow%3 == 0:
                baseColor = QtGui.QColor(255,190,190)
            elif parentRow%3 == 1:
                baseColor = QtGui.QColor(190,255,190)
            elif parentRow%3 == 2:
                baseColor = QtGui.QColor(230,230,175)
            baseColor2 = baseColor.lighter(110)
            if row%2:
                return baseColor
            else:
                return baseColor2
        return super(BlockModel, self).data(index, role)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """
        Overrided setData method
        """
        row = index.row()
        col = index.column()
        item = self.itemFromIndex(index)

        if role==QtCore.Qt.CheckStateRole:
            return self.setData(index,value)

        if isinstance(item, self.PropertyItem):
            if item.datatype == int:
                val = value.toInt()[0]
            elif item.datatype == bool:
                val = value.toBool()
            elif item.datatype == float:
                val = value.toDouble()[0]
            elif issubclass(item.datatype, BaseEnum):
                val = item.datatype(unicode(value.toString()))
            else:
                val = unicode(value.toString()).strip()
            parent_name = str(self.itemFromIndex(index.parent()).text())
            name = str(self.itemFromIndex(index.sibling(row,0)).text())
            if not isinstance(val, unicode) or val:
                self.data_dict[parent_name][name] = val
            self.apply()
            self.update(self.block,update_view=False)
            value = unicode(self.data_dict[parent_name][name])
        return super(BlockModel, self).setData(index, value, role)


# CustomDelegate Class Definition
class CustomDelegate(QtGui.QStyledItemDelegate):
    """
    Custom Delegate to create custom editors for special data types
    """
    def createEditor(self, parent, option, index):
        """
        Create custom editors for special data types
        """
        item = index.model().itemFromIndex(index)
        if isinstance(item, BlockModel.PropertyItem):
            # ComboBox for enumeration
            if issubclass(item.datatype, BaseEnum):
                editor = QtGui.QComboBox(parent)
                editor.addItems(item.datatype.values)
                current_value = unicode(index.data().toString())
                current_index = editor.findText(current_value)
                if current_index != -1:
                    editor.setCurrentIndex(current_index)
                self.updateEditorGeometry(editor, option, index)
                editor.showPopup()
                return editor
            # Custom SpinBox for floats
            elif item.datatype == float:
                editor = QtGui.QDoubleSpinBox(parent)
                editor.setDecimals(3)
                editor.setRange(-5000000,5000000)
                return editor
            # Custom ComboBox for SequenceID property
            elif item.is_sequence_id:
                editor = QtGui.QComboBox(parent)
                main_editor = parent.parent().model().editor
                current_sub = main_editor.get_current_sequence_item().sequence
                sub_list = [sub.sequence_id for sub in current_sub.subsequences]
                sub_list.append(BlockProperties.DEFAULT_VALUES[XSA.SEQUENCEID])
                editor.addItems(sub_list)
                current_id = index.data().toString()
                current_index = editor.findText(current_id)
                if current_index != -1:
                    editor.setCurrentIndex(current_index)
                self.updateEditorGeometry(editor, option, index)
                editor.showPopup()
                return editor
        return super(CustomDelegate, self).createEditor(parent, option, index)

    def setModelData(self, editor, model, index):
        """
        Fixes QComboBox user property bug in Qt 4.8.2
        Not required for Qt >= 4.8.4
        """
        if isinstance(editor, QtGui.QComboBox):
            value = QtCore.QVariant(editor.currentText())
            model.setData(index, value)
        else:
            QtGui.QStyledItemDelegate.setModelData(self, editor, model, index)
