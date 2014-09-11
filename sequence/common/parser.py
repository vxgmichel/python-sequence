# -*- coding: utf-8 -*-

""" Module for sequence parsing """

#-------------------------------------------------------------------------------
# Name:        XMLSequence
# Purpose:     Module for sequence parsing
#
# Author:      michel.vincent
#
# Created:     27/09/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Imports
from collections import OrderedDict
from lxml import etree as ET
from StringIO import StringIO
import re


# Import from packages
from sequence.common.constant import XSM, XBM, XSA
try: from sequence.action.abstract import create_action
except: pass


# XML Sequence class definition
class XMLSequence():
    """
    Class to manipulate an XML sequence
    """

    VALID_BLOCKS = [getattr(XBM, x)
                    for x in dir(XBM)
                    if not x.startswith('__')]

    MAX_DEPTH = float('inf')

    def __init__(self, sequence_id, depth=0, level=0, execution=False):
        """
        Initialize the sequence

        :param sequence_id: str -- ID of the sequence
        :param depth: int -- depth of the sequence through the backup chain
        :param level: int -- level of the sequence (depth + subsequence)
        :param execution: boolean -- indicate to prepare sequence for execution
        """
        self.sequence_id = sequence_id
        self.depth = depth
        self.level = level
        self.blocks = []
        self.subsequences = []
        self.backup = None
        self.begin = None
        self.end = []
        self.execution = execution
        self.extra = {}

    def set_backup(self, backup):
        """
        Set a custom backup to the sequence
        """
        if self.backup is not None:
            self.subsequences.remove(self.backup)
        self.backup = backup
        self.subsequences.append(backup)

    def parse_sequence(self, node):
        """
        Parse an xml node as a sequence
        """
        nodes_dict = {XSM.BLOCKS: None,
                      XSM.SUBSEQUENCES: None,
                      XSM.BACKUP: None}
        # Get main nodes
        for sub_node in node:
            if sub_node.tag in nodes_dict:
                if nodes_dict[sub_node.tag] is not None:
                    msg = u"More than one node {} is found in the same sequence"
                    msg = msg.format(sub_node.tag)
                    raise SequenceSynthaxError(msg)
                nodes_dict[sub_node.tag] = sub_node
            elif sub_node.tag == XSM.EXTRA:
                self.extra.update(sub_node.attrib)
            else :
                msg = u"Unknow markup in sequence {}: {}"
                msg = msg.format(self.sequence_id, sub_node.tag)
                raise SequenceSynthaxError(msg)
        # Parse sequence blocks
        self.parse_blocks(nodes_dict[XSM.BLOCKS])
        # Create links
        self.create_links()
        # Check sequence
        if self.execution:
            self.check_sequence()
        # Create actions
        self.create_actions()
        # Parse subsequence
        self.parse_subsequences(nodes_dict[XSM.SUBSEQUENCES])
        # Parse Backup
        self.parse_backup(nodes_dict[XSM.BACKUP], nodes_dict[XSM.SUBSEQUENCES])

    def parse_blocks(self, node):
        """
        Parse an xml node as list of blocks
        """
        id_list = []
        for sub_node in node:
            if sub_node.tag in self.VALID_BLOCKS:
                if XSA.ID not in sub_node.keys():
                    msg = u"A block appears to have no ID attribute"
                    raise SequenceSynthaxError(msg)
                block_id = sub_node.attrib[XSA.ID]
                if block_id in id_list:
                    msg = u"More than one block with the ID : {}"
                    msg = msg.format(block_id)
                    raise SequenceSynthaxError(msg)
                id_list.append(block_id)
                block = XMLBlock(block_id, sub_node.tag)
                block.parse_block(sub_node)
                self.blocks.append(block)



    def parse_subsequences(self, node):
        """
        Parse an xml node as list of subsequences
        """
        # Find all subsqeuqences
        subsequences_dict = {}
        if node is not None:
            for subsequence in node:
                sequence_id = is_sequence(subsequence)
                if sequence_id:
                    if sequence_id in subsequences_dict:
                        msg = u"More than one subsequence with the ID : {}"
                        msg = msg.format(sequence_id)
                        raise SequenceSynthaxError(msg)
                    subsequences_dict[sequence_id] = subsequence
        # Create useful subsequences
        sub_created = {}
        for block in self.blocks:
            if block.block_type == XBM.MACRO:
                sub_id = block.properties.sequence_id
                if sub_id in subsequences_dict:
                    block.subsequence = XMLSequence(sub_id, level=self.level+1,
                                                    execution=self.execution)
                    sub = subsequences_dict.pop(sub_id)
                    block.subsequence.parse_sequence(sub)
                    self.subsequences.append(block.subsequence)
                    sub_created[sub_id] = block.subsequence
                elif sub_id in sub_created:
                    block.subsequence = sub_created[sub_id]
                elif sub_id != BlockProperties.DEFAULT_VALUES[XSA.SEQUENCEID]:
                    msg = u"There is no subsequence called {}"
                    msg = msg.format(sub_id)
                    raise SequenceSynthaxError(msg)
        # Create useless subsequences
        if not self.execution:
            for sub_id, xml in subsequences_dict.items():
                sub = XMLSequence(sub_id, level=self.level+1)
                sub.parse_sequence(xml)
                self.subsequences.append(sub)

    def parse_backup(self, backup_node, subsequence_node):
        """
        Parse an xml node as a backup sequence

        :param backup_node: xml node of the backup sequence reference
        :param subsequence_node: xml node of the subsequences list
        """
        # Return if a backup is already defined or depth limit reached
        if self.backup is not None or self.depth >= self.MAX_DEPTH:
            return
        # Return if no backup defined
        if backup_node is None:
            return
        # Get the backup ID
        try :
            backup_id = backup_node.attrib[XSA.SEQUENCEID]
        except KeyError:
            msg = u"The markup '{}' appears to have no '{}' attribute"
            msg = msg.format(XSM.BACKUP, XSA.SEQUENCEID)
            raise SequenceSynthaxError(msg)
        # Test if there is subsequences to use
        if subsequence_node is None:
            msg = u"There is no subsequences to use for backup"
            raise SequenceSynthaxError(msg)
        # Get the subsequence corresponding
        try:
            # In a non-execution case, the subsequence has already been created
            if not self.execution:
                # Set the backup sequence and return
                self.backup = next(subsequence
                                   for subsequence in self.subsequences
                                   if subsequence.sequence_id == backup_id)
                return
            else:
                # Find the corresponding node
                backup = next(subsequence
                              for subsequence in subsequence_node
                              if backup_id == is_sequence(subsequence))
        except StopIteration:
            msg = u"There is no subsequence called {} for backup"
            msg = msg.format(backup_id)
            raise SequenceSynthaxError(msg)
        # Create the backup sequence
        backup_sequence = XMLSequence(backup_id, depth=self.depth+1,
                                      level=self.level+1,
                                      execution=self.execution)
        backup_sequence.parse_sequence(backup)
        # Set the backup sequence
        self.subsequences.append(backup_sequence)
        self.backup = backup_sequence

    def create_links(self):
        """
        Create links between blocks
        """
        for first_block in self.blocks:
            if first_block.outputs:
                for out in first_block.outputs:
                    try :
                        second_block = next(b for b in self.blocks
                                            if b.block_id == out)
                    except StopIteration :
                        msg = u"The block {} references a non-existing block "
                        msg += "({})"
                        msg = msg.format(first_block.block_id, out)
                        raise SequenceSynthaxError(msg)
                    if first_block.block_id not in second_block.inputs :
                        msg = u"Reciprocity Error between blocks '{}' and '{}'"
                        msg = msg.format(first_block.block_id,
                                         second_block.block_id)
                        raise SequenceSynthaxError(msg)
                    index = first_block.outputs.index(second_block.block_id)
                    first_block.outputs[index] = second_block
                    index = second_block.inputs.index(first_block.block_id)
                    second_block.inputs[index] = first_block

    def create_actions(self):
        """
        Create actions (only for execution)
        """
        for block in self.blocks:
            if block.block_type == XBM.ACTION:
                block.create_action()

    def check_sequence(self):
        """
        Check sequence validity (only for execution)
        """
        # Check number of begin and end blocks
        count_begin = count_end = 0
        for block in self.blocks :
            if block.block_type == XBM.BEGIN:
                self.begin = block
                count_begin += 1
            if block.block_type == XBM.END:
                self.end.append(block)
                count_end += 1
        if count_begin == 0 :
            msg = u"No Begin block"
            raise InvalidSequenceError(msg)
        if count_begin > 1 :
            msg = u"More than one Begin block"
            raise InvalidSequenceError(msg)
        if count_end == 0 :
            msg = u"No End block"
            raise InvalidSequenceError(msg)
        # Check for broken links
        for block in self.blocks:
            if block.outputs:
                for out in block.outputs:
                    if not isinstance(out, XMLBlock):
                        msg = u"Couldn't link the block '{}' to '{}'"
                        msg = msg.format(block.block_id, out)
                        raise InvalidSequenceError(msg)
            if block.inputs:
                for inp in block.inputs:
                    if not isinstance(inp, XMLBlock):
                        msg = u"Couldn't link the block '{}' to '{}'"
                        msg = msg.format(block.block_id, inp)
                        raise InvalidSequenceError(msg)
        # Check for circular links
        current  = self.begin
        blocks = []
        blocks = self.recursive_check(current, blocks)
        # Check for excluded blocks
        diff = len(self.blocks) - len(blocks)
        if diff != 0:
            msg = u"{} block(s) are excluded from the main sequence"
            msg = msg.format(diff)
            raise InvalidSequenceError(msg)

    def recursive_check(self, current, blocks):
        if current in blocks:
            msg = u"A circular link involves the block '{}'"
            msg = msg.format(current.block_id)
            raise InvalidSequenceError(msg)
        blocks = list(blocks) + [current]
        if current.outputs is None:
            return blocks
        return {block
                    for outputs in current.outputs
                        for block in self.recursive_check(outputs, blocks)}

    def get_element(self):
        """
        Build and return the XML node corresponding to the sequence
        """
        # Init block element
        attrib = {XSA.SEQUENCEID : self.sequence_id}
        sequence_element = ET.Element(XSM.SEQUENCE, attrib)
        # Append blocks element
        blocks_element = ET.Element(XSM.BLOCKS)
        for block in self.blocks:
            blocks_element.append(block.get_element())
        sequence_element.append(blocks_element)
        # Append subsequences element
        if self.subsequences:
            subsequences_element = ET.Element(XSM.SUBSEQUENCES)
            for subsequence in self.subsequences:
                subsequences_element.append(subsequence.get_element())
            sequence_element.append(subsequences_element)
        # Append backup element
        if self.backup:
            attrib = {XSA.SEQUENCEID : self.backup.sequence_id}
            sequence_element.append(ET.Element(XSM.BACKUP, attrib))
        # Return
        return sequence_element

    def xml_export(self, filename, pretty=True):
        """
        Export XML Sequence to an XML file
        """
        # Convert Element to ElementTree
        sequence_element = ET.ElementTree(self.get_element())
        # Choose the target
        if pretty:
            target = StringIO()
        else:
            target = filename
        # Write the target
        sequence_element.write(target, xml_declaration = True,
                               encoding="UTF-8", pretty_print = True)
        # Use custom formatter if required
        if pretty:
            data = StringIO(target.getvalue())
            target.close()
            with open(filename,'w') as output_file:
                custom_format_sequence(data, output_file)
            data.close()

    def remove_block(self, block):
        """
        Remove a block from the block list and break the links
        """
        self.blocks.remove(block)
        if block.inputs:
            for inp in block.inputs:
                inp.outputs.remove(block)
        if block.outputs:
            for out in block.outputs:
                out.inputs.remove(block)


# XML Block class definition
class XMLBlock():
    """
    Class to manipulate an XML block
    """

    # Test dictionnary for xml block validity
    # 0 is absent, 1 is present, 2 is not limited
    # Inputs, Outputs, Property :    I  O  P
    TEST_DICT = {XBM.BEGIN:         [0, 1, 0],
                 XBM.END:           [1, 0, 0],
                 XBM.ACTION:        [1, 1, 1],
                 XBM.MACRO:         [1, 1, 1],
                 XBM.BRANCH:        [2, 2, 1],
                 XBM.TIMEINIT:      [1, 1, 0],
                 XBM.WAIT:          [1, 1, 1]}

    def __init__(self, block_id, block_type):
        """
        Initialize the XML block

        :param block_id: str -- block ID
        :param block_type: str -- type of the block
        """
        self.block_id = block_id
        self.block_type = block_type
        self.inputs = None
        if self.TEST_DICT[block_type][0]:
            self.inputs = []
        self.outputs = None
        if self.TEST_DICT[block_type][1]:
            self.outputs = []
        self.subsequence = None
        self.properties = BlockProperties(block_type)
        self.parameters = {}
        self.action = None
        self.extra = {}

    def parse_block(self, node):
        """
        Parse an XML node as a block
        """
        for sub_node in node :
            if sub_node.tag == XSM.INPUTOUTPUT:
                self.parse_io(sub_node)
            elif sub_node.tag == XSM.PROPERTIES:
                self.properties.parse_properties(sub_node)
            elif sub_node.tag == XSM.PARAMETERS:
                self.parameters = dict(sub_node.attrib)
            elif sub_node.tag == XSM.EXTRA:
                self.extra.update(sub_node.attrib)
            else :
                msg = u"Unknow markup in block {}: {}"
                msg = msg.format(self.block_id, sub_node.tag)
                raise SequenceSynthaxError(msg)
        self.check_type()

    def parse_io(self, node):
        """
        Parse an XML node as input/output data
        """
        if XSA.INPUT in node.keys():
            string = node.attrib[XSA.INPUT]
            self.inputs.extend([x.strip() for x in string.split(';') if x])
        if XSA.OUTPUT in node.keys():
            string = node.attrib[XSA.OUTPUT]
            self.outputs.extend([x.strip() for x in string.split(';') if x])

    def check_type(self):
        """
        Check block validity
        """
        tab = [self.inputs, self.outputs]
        names = ['input','ouput']
        test = self.TEST_DICT[self.block_type]
        for i in range(2):
            if tab[i] and not test[i]:
                msg = u"The block {} souldn't have an {}"
                msg = msg.format(self.block_id, names[i])
                raise SequenceSynthaxError(msg)
            if tab[i] is None and test[i]:
                msg = u"The block {} sould have an {}"
                msg = msg.format(self.block_id, names[i])
                raise SequenceSynthaxError(msg)
            if tab[i] and len(tab[i])>1 and test[i] != 2:
                msg = u"The block {} souldn't have more than one {}"
                msg = msg.format(self.block_id, names[i])
                raise SequenceSynthaxError(msg)
        self.properties.check_type(self.block_type, self.block_id)

    def get_element(self):
        """
        Build and return the XML node corresponding to the block
        """
        # Init block element
        block_element = ET.Element(self.block_type, {XSA.ID : self.block_id})
        # Get IO strings
        io_attrib = {}
        if self.inputs is not None:
            io_attrib[XSA.INPUT] = ";".join(inp.block_id.strip()
                                            if isinstance(inp, XMLBlock)
                                            else inp for inp in self.inputs)
        if self.outputs is not None:
            io_attrib[XSA.OUTPUT] = ";".join(out.block_id.strip()
                                             if isinstance(out, XMLBlock)
                                             else out for out in self.outputs)
        # Build block element
        block_element.append(ET.Element(XSM.INPUTOUTPUT, io_attrib))
        if self.properties:
            block_element.append(self.properties.get_element())
        if self.parameters:
            params = {key:unicode(value)
                          for key,value in self.parameters.iteritems()}
            block_element.append(ET.Element(XSM.PARAMETERS, params))
        if self.extra:
            block_element.append(ET.Element(XSM.EXTRA, self.extra))
        # Return
        return block_element

    def handle_multiple_inputs(self):
        """
        Return True if the block handles multiple inputs
        """
        return self.TEST_DICT[self.block_type][0] > 1

    def handle_multiple_outputs(self):
        """
        Return True if the block handles multiple outputs
        """
        return self.TEST_DICT[self.block_type][1] > 1

    def create_action(self):
        """
        Create action from Actions module
        """
        self.action = create_action(self)


# Block properties class definition
class BlockProperties():
    """
    Class to manipulate block properties
    """

    # XML Attributes to class attributes
    ATTR_DICT = OrderedDict([(XSA.MODULE,'module'),
                             (XSA.ITERATION,'iteration'),
                             (XSA.TICK,'tick'),
                             (XSA.TIME,'time'),
                             (XSA.ABSOLUTE,'absolute'),
                             (XSA.SEQUENCEID,'sequence_id')])

    DEFAULT_VALUES = OrderedDict([(XSA.MODULE, u'EmptyModule'),
                                  (XSA.ITERATION, 1),
                                  (XSA.TICK, 0.0),
                                  (XSA.TIME, 1.0),
                                  (XSA.ABSOLUTE, True),
                                  (XSA.SEQUENCEID,u'NoSubsequence')])

    # Test dictionnary for xml block validity
    # 0 is absent, 1 is present
    # Module, Iteration, Tick ... :  M  I  T  T  A  S
    TEST_DICT = {XBM.BEGIN:         [0, 0, 0, 0, 0, 0],
                 XBM.END:           [0, 0, 0, 0, 0, 0],
                 XBM.ACTION:        [1, 1, 1, 0, 0, 0],
                 XBM.MACRO:         [0, 1, 1, 0, 0, 1],
                 XBM.BRANCH:        [0, 0, 0, 0, 0, 0],
                 XBM.TIMEINIT:      [0, 0, 0, 0, 0, 0],
                 XBM.WAIT:          [0, 0, 0, 1, 1, 0]}

    def __init__(self, block_type):
        """
        Initialize the block properties
        """
        for index, (name, attr) in enumerate(self.ATTR_DICT.items()):
            if self.TEST_DICT[block_type][index]:
                setattr(self, attr, self.DEFAULT_VALUES[name])
            else:
                setattr(self, attr, None)

    def parse_properties(self, node):
        """
        Parse an xml node as block properties
        """
        dictionary = {}
        for name, value in node.attrib.items() :
            if name in self.ATTR_DICT:
                cast = type(self.DEFAULT_VALUES[name])
                try:
                    if cast != bool:
                        dictionary[name] = cast(value)
                    else:
                        if value.lower() in ["true","1"]:
                            dictionary[name] = True
                        elif value.lower() in ["false","0"]:
                            dictionary[name] = False
                        else:
                            raise Exception()
                except:
                    msg = u"Couldn't cast {} = {} to {}"
                    msg = msg.format(name, value, cast)
                    raise SequenceSynthaxError(msg)
            else :
                msg = u"Unknow property : {}".format(name)
                raise SequenceSynthaxError(msg)
        self.set_dictionary(dictionary)

    def set_dictionary(self, dictionary):
        """
        Set the dictionnary as the block properties
        Return True if the dictionary has been modified
        """
        boolean = False
        for name, value in dictionary.items():
            boolean = boolean or getattr(self, self.ATTR_DICT[name]) != value
            setattr(self, self.ATTR_DICT[name], value)
        return boolean

    def get_element(self):
        """
        Return XML element of the block properties
        """
        attrib = {name:unicode(value)
                  for name, value in self.get_dictionnary().items()}
        return ET.Element(XSM.PROPERTIES, attrib)

    def get_dictionnary(self):
        """
        Return a dictionnary of the block properties
        """
        return {name: getattr(self,attr)
                  for name, attr in self.ATTR_DICT.items()
                  if getattr(self,attr) is not None}

    def check_type(self, block_type, block_id):
        """
        Check properties validity

        :param block_type: type of the block to use for checking
        :param block_id: ID of the block (for error message)
        """
        test_list = self.TEST_DICT[block_type]
        tab = [XSA.MODULE, XSA.ITERATION, XSA.TICK,
               XSA.TIME, XSA.ABSOLUTE, XSA.SEQUENCEID]
        for i, attr in enumerate(tab):
            if getattr(self, self.ATTR_DICT[attr]) and not test_list[i]:
                msg = u"The block '{}' souldn't have a property '{}'"
                msg = msg.format(block_id, attr)
                raise SequenceSynthaxError(msg)
            if getattr(self, self.ATTR_DICT[attr]) is None and test_list[i]:
                msg = u"The block '{}' sould have a property '{}'"
                msg = msg.format(block_id, attr)
                raise SequenceSynthaxError(msg)

    def __bool__(self):
        """
        Boolean cast
        """
        return any(getattr(self, value) is not None
                   for value in self.ATTR_DICT.values())
    __nonzero__ = __bool__


# Sequence Synthax Error class definition
class SequenceSynthaxError(SyntaxError):
    """
    Custom error raised when a synthax error is detected
    """

    def __init__(self, strerror) :
        SyntaxError.__init__(self, strerror)
        self.strerror = strerror

    def __str__(self):
        return self.strerror

    def __unicode__(self):
        return u"Sequence Synthax Error : " + unicode(self.strerror)



# Invalid Sequence Error class definition
class InvalidSequenceError(StandardError):
    """
    Custom error raised when the sequence is invalid
    """

    def __init__(self, strerror) :
        StandardError.__init__(self, strerror)
        self.strerror = strerror

    def __str__(self) :
        return self.strerror

    def __unicode__(self):
        return u"Invalid Sequence Error : " + unicode(self.strerror)


# Parse an xml sequence file
def parse_sequence_file(file_name, max_depth=None,
                        backup_file=None, execution=True):
    """
    Parse an XML sequence file

    :param file_name: str -- name of the file to parse as a sequence
    :param max_depth: int -- maximum depth for sequence creation
    :param backup_file: str -- name of the file to parse as a backup sequence
    :return: the XMLSequence corresponding
    """
    # Apply maximum depth
    if max_depth:
        XMLSequence.MAX_DEPTH = max_depth
    else:
        XMLSequence.MAX_DEPTH = float('inf')
    # Create sequence
    tree = ET.parse(file_name)
    root = tree.getroot()
    sequence_id = is_sequence(root)
    if not sequence_id :
        msg = u"Root is not sequence"
        raise SequenceSynthaxError(msg)
    sequence = XMLSequence(sequence_id, execution=execution)
    # Create backup sequence
    if backup_file and XMLSequence.MAX_DEPTH > 0:
        backup_tree = ET.parse(backup_file)
        backup_root = backup_tree.getroot()
        backup_id = is_sequence(root)
        if not backup_id :
            msg = u"Backup root is not sequence"
            raise SequenceSynthaxError(msg)
        sequence.set_backup(XMLSequence(backup_id, depth=1,
                                        execution=execution))
    # Parse sequence
    sequence.parse_sequence(root)
    # Parse backup sequence
    if backup_file and XMLSequence.MAX_DEPTH > 0:
        sequence.backup.parse_sequence(backup_root)
    # Return
    return sequence


# Is-sequence test
def is_sequence(node):
    """
    Test if a node is a sequence, and return its ID
    """
    if node.tag != XSM.SEQUENCE:
        return False
    # Check for sequence ID
    if XSA.SEQUENCEID not in node.keys():
        msg = u"A sequence appears to have no haveSequenceID"
        raise SequenceSynthaxError(msg)
    # Assert sequence ID
    sequence_id = node.attrib[XSA.SEQUENCEID]
    assert_valid_id(sequence_id, XSA.SEQUENCEID)
    return sequence_id


# Assert valid IDs
def assert_valid_id(string, display_name):
    """
    Assert valid IDs

    :param string: str -- string to assert
    :param display_name: str -- string to display with error message"""
    pattern = r'[/\~<>]'
    if re.search(pattern, string):
        msg = u"Invalid " + display_name
        msg += u" ({})".format(string)
        raise SequenceSynthaxError(msg)


def custom_format_sequence(in_file, out_file):
    """
    Format a sequence xml file with a custom format

    :param in_file: sequence file written with the pretty print option of lxml
    :param out_file: file object to write the formatted sequence
    """
    # Handle the header of the file
    out_file.write(in_file.readline()+'\n')
    # Boolean to tell if the cursor is inside a sequence block
    inside_action = False
    # Loop over the lines in the input file
    for line in in_file:
        # Remove the line break
        line = line.strip('\n')
        # Find the index of a possible ID attribute
        index_id = line.find(XSA.SEQUENCEID)
        if index_id == -1:
            index_id = line.find(XSA.ID)
        # Intitialize list of groups to write over different lines
        groups = []
        # Initialize the current group
        current_group = ""
        # Initialize the boolean to tell if the cursor is inside a quote
        inside_quote = False
        # Initialize the counter of space for indentation
        nb_indent = 0
        # Loop over the characters in the line
        for index, char in enumerate(line):
            if char != ' ' or inside_quote or \
               (index==index_id-1 and not inside_action):
                # Append the character to the current group
                current_group += char
            elif char == ' ' and not inside_quote:
                if current_group != "":
                    # Append the current group to the group list
                    groups.append(current_group)
                    current_group = ""
                elif len(groups) == 0:
                    # Increment number of spaces for indentation
                    nb_indent += 1
            if char == '"':
                # Toogle the inside quote boolean
                inside_quote ^= True
        # Append the last group to the group list
        if current_group:
            groups.append(current_group)
        # Write the first line with a 2*nb indentation
        out_file.write(' '*(nb_indent*2)+groups[0]+'\n')
        for group in groups[1:] :
            # Write the other lines with a 2*(nb+2) indentation
            out_file.write(' '*((nb_indent+2)*2)+group+'\n')
        if any(groups[0].find(getattr(XBM, name)) in (1, 2)
               for name in dir(XBM) if not name.startswith('__')):
            # Toogle the inside action boolean
            inside_action ^= True
        # Add an additional break line if inside an action
        if not inside_action:
            out_file.write('\n')

