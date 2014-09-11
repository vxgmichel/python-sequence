# -*- coding: utf-8 -*-

""" Module for running sequences """

#-------------------------------------------------------------------------------
# Name:        RunableSequence
# Purpose:     Module for running sequences
#
# Author:      michel.vincent
#
# Created:     02/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
#-------------------------------------------------------------------------------


# Imports
from threading import Thread, Event
from time import sleep
from timeit import default_timer as time
from sequence.common.constant import XBM, LOGGER, BES
from sequence.action.abstract import create_action

# Runable Sequence class definition
class RunableSequence():
    """ Class for creating runable sequences and subsequences """

    class TimeReference():
        """ Class for creating a specific time reference """

        def __init__(self):
            """ Initializer the time reference """
            self.ref = time()

        def reset(self):
            """ Reset the time reference """
            self.ref = time()

        def wait(self, time):
            """ Wait until the time reference equals the time parameter """
            delta = time + self.ref -  time()
            while delta > 0:
                sleep(delta)
                delta = time + self.ref -  time()

    def __init__(self, xml_sequence, stop_thread, root=False):
        """ Initialize a runable sequence

        :param xml_sequence: xml sequence to get a runable sequence from
        :param stop_thread: the stop mecansim to associate
        :param root: True if assiociated to a RootSequenceThread
        """
        self.xml_sequence = xml_sequence
        self.threads = []
        self.branch_dict = {}
        self.starter = Event()
        self.end_threads = []
        self.backup = None
        self.root = root
        self.time_ref = self.TimeReference()
        self.stop_thread = stop_thread
        self.stop_thread.add_starter(self.starter)
        self.load()

    def load(self):
        """ Load the content of the XML sequence """
        stack = [SequenceThread(self)]
        threads = []
        # Thread loop
        while stack:
            # Pop next thread elements
            thread = stack.pop()
            # Block loop
            while not thread.is_complete:
                # Build chain
                thread.build_execution()
                # Thread stacking
                stack.extend(thread.generate_threads())
                # Increment
                thread.increment()
            # Add the thread
            threads.append(thread)
        # Save threads
        self.threads = threads
        # Add all concerned threads to the branch executions related
        for thread in self.threads:
            if thread.current_block in self.branch_dict:
                self.branch_dict[thread.current_block].add_thread(thread)
        # Load backup_sequence:
        if self.xml_sequence.backup:
            self.backup = RootSequenceThread(self.xml_sequence.backup,
                                                      self.stop_thread)

    def run(self):
        """ Run the sequence """
        for thread in self.threads:
            thread.start()
        self.time_ref.reset()
        self.starter.set()
        res = True
        for end_thread in self.end_threads:
            end_thread.join()
            res &= end_thread.return_value
        return res


# Beautiful Decorator
def logdecorator(f):
    def wrapper(self, *args, **kwargs):
        LOGGER.debug(BES.BG, extra=self.log_dict)
        res = f(self, *args, **kwargs)
        if res:
            LOGGER.debug(BES.OK, extra=self.log_dict)
        else:
            LOGGER.debug(BES.KO, extra=self.log_dict)
        return res
    return wrapper


# Execution classes definition
class AbstractExecution():
    """
    Class providing a basis for execution implementation
    """

    def __init__(self, thread):
        """
        Initialize the execution with the parent thread
        """
        self.thread = thread
        self.level = thread.sequence.xml_sequence.level
        self.block = thread.current_block
        self.time_ref = thread.sequence.time_ref
        self.stop_thread = thread.stop_thread
        self.log_dict = {'sequenceID': thread.sequence.xml_sequence.sequence_id,
                         'ID':    self.block.block_id,
                         'level': self.level,
                         'type':  self.block.block_type.upper()}

    @logdecorator
    def execute(self):
        """
        Method to override
        """
        LOGGER.info(None, extra=self.log_dict)
        return True


class BranchExecution(AbstractExecution):
    """
    Class implementing a branch execution
    """

    def __init__(self, thread):
        """
        Initialize the execution with the parent thread
        """
        AbstractExecution.__init__(self, thread)
        self.wait_list = []
        self.event = Event()
        self.stop_thread.add_starter(self.event)

    def add_thread(self, thread):
        """
        Append a thread to join to the list
        """
        if thread not in self.wait_list:
            self.wait_list.append(thread)

    @logdecorator
    def execute(self):
        """
        Run the execution
        """
        for thread in self.wait_list:
            thread.join()
        if len(self.block.inputs) > 1:
            msg = "The {} threads have met".format(len(self.block.inputs))
            LOGGER.info(msg, extra=self.log_dict)
        if len(self.block.outputs) > 1:
            msg = "{} threads have been started".format(len(self.block.outputs))
            LOGGER.info(msg, extra=self.log_dict)
        self.event.set()
        return True

class ResetTimeExecution(AbstractExecution):
    """
    Class implementing a time reset execution
    """

    @logdecorator
    def execute(self):
        """
        Run the execution
        """
        self.time_ref.reset()
        LOGGER.info(None, extra=self.log_dict)
        return True

class WaitExecution(AbstractExecution):
    """
    Class implementing a wait execution
    """

    def __init__(self, thread):
        """
        Initialize the execution with the parent thread
        """
        AbstractExecution.__init__(self, thread)
        self.time = self.block.properties.time
        self.absolute = self.block.properties.absolute

    @logdecorator
    def execute(self):
        """
        Run the execution
         """
        if self.absolute:
            msg = 'Wait for t={}s'.format(self.time)
            LOGGER.info(msg, extra=self.log_dict)
            self.time_ref.wait(self.time)
        else :
            msg = 'Wait {}s'.format(self.time)
            LOGGER.info(msg, extra=self.log_dict)
            sleep(self.time)
        LOGGER.info('Done', extra=self.log_dict)
        return True

class ActionExecution(AbstractExecution):
    """
    Class implementing an action execution
    """
    def __init__(self, thread):
        """
        Initialize the execution with the parent thread
        """
        AbstractExecution.__init__(self, thread)
        self.action = create_action(self.block)

    @logdecorator
    def execute(self):
        """
        Run the execution
        """
        return self.action.execute(self.stop_thread, self.log_dict)

class SubsequenceExecution(AbstractExecution):
    """
    Class implementing a subsequence execution
    """

    def __init__(self, thread):
        """
        Initialize the execution with the parent thread
        """
        AbstractExecution.__init__(self, thread)
        self.sequences = []
        self.tick = self.block.properties.tick
        self.iteration = self.block.properties.iteration
        self.sequence_id = self.block.subsequence.sequence_id
        if self.block.subsequence:
            self.sequences = [RunableSequence(self.block.subsequence,
                                              self.thread.stop_thread)
                              for _ in range(self.iteration)]

    @logdecorator
    def execute(self):
        """
        Run the execution
        """
        if not self.sequences:
            msg = u"No subsequence to run"
            LOGGER.info(msg, extra=self.log_dict)
            return True
        for i, sequence in enumerate(self.sequences):
            msg = u"Call : {} ".format(self.sequence_id)
            if self.iteration > 1:
                msg += u"(iteration {})".format(i+1)
            LOGGER.info(msg, extra=self.log_dict)
            if not sequence.run():
                return False
            if self.tick:
                msg = 'Tick ({}s)'.format(self.tick)
                LOGGER.info(msg, extra=self.log_dict)
                sleep(self.tick)
        return True


# SequenceThread class definition
class SequenceThread(Thread):
    """
    Class to implement and execute a sequence thread
    """

    # Class dictionnary
    CLASS_DICT = {XBM.BEGIN     : AbstractExecution,
                  XBM.END       : AbstractExecution,
                  XBM.ACTION    : ActionExecution,
                  XBM.BRANCH    : BranchExecution,
                  XBM.TIMEINIT  : ResetTimeExecution,
                  XBM.WAIT      : WaitExecution,
                  XBM.MACRO     : SubsequenceExecution}

    # Methods for thread creation
    def __init__(self, sequence, starter=None, first=None):
        """
        Initialize the sequence thread
        """
        Thread.__init__(self)
        # Sequence attribute
        self.sequence = sequence
        self.stop_thread = sequence.stop_thread
        # Starter event and current block attributes
        self.is_complete = False
        if starter:
            self.starter = starter
            self.current_block = first
        else :
            self.starter = sequence.starter
            self.current_block = self.sequence.xml_sequence.begin
        # Execution chain attribute
        self.execution_chain = []
        self.return_value = None

    def build_execution(self):
        """
        Build the next execution block of the sequence thread
        """
        # Build the next execution
        execution_type = self.CLASS_DICT[self.current_block.block_type]
        execution = execution_type(self)
        self.execution_chain.append(execution)
        # Append branch execution to branch dict for future update
        if isinstance(execution, BranchExecution):
            self.sequence.branch_dict[self.current_block] = execution

    def generate_threads(self):
        """
        Generate the threads launched by the current sequence thread
        """
        tab = []
        # Create the threads launched by the current thread
        if self.current_block.outputs is not None:
            for block in self.current_block.outputs[1:]:
                starter = self.execution_chain[-1].event
                tab.append(SequenceThread(self.sequence, starter, block))
        # Return the list
        return tab

    def increment(self):
        """
        Go to the next block
        """
        if self.current_block.outputs:
            first_of_last = self.current_block.outputs[0].inputs[-1].block_id
            self.is_complete = not self.current_block.block_id == first_of_last
            self.current_block = self.current_block.outputs[0]
        else:
            self.sequence.end_threads.append(self)
            self.is_complete = True
            self.current_block = None

    # Method Thread execution
    def run(self):
        """
        Run method of the sequence thread
        """
        # Wait for thread starter
        self.starter.wait()
        # Forced stop case
        if self.stop_thread.is_set():
            self.return_value = False
            return
        # Execution loop
        for ex in self.execution_chain:
            # Forced stop case
            if self.stop_thread.is_set():
                self.stop_thread.add_backup(self.sequence.backup)
                self.return_value = False
                return
            # Loop execution
            res = ex.execute()
            # Result test
            if not res :
                if not self.stop_thread.is_set():
                    self.stop_thread.set()
                self.stop_thread.add_backup(self.sequence.backup)
                self.return_value = False
                return
        # Regular return
        self.return_value = True
        return


# Stop thread class definition
class StopThread(Thread):
    """
    Class implementing a mechanism to stop the whole sequence execution
    """

    def __init__(self, main_thread):
        """
        Initialize the stop thread
        """
        Thread.__init__(self)
        self.enable_flag = False
        self.backup_list = []
        self.starters = []
        self.children = []
        self.main_thread = main_thread
        xml_sequence = main_thread.xml_sequence
        self.log_dict = {'sequenceID': xml_sequence.sequence_id,
                         'ID':         self.name,
                         'level':      xml_sequence.level,
                         'type':       "STOP"}

    def enable(self):
        """
        Enable the stop mechanism
        """
        self.enable_flag = True

    def disable(self):
        """
        Disable the stop mechanism
        """
        self.enable_flag = False

    def add_starter(self, starter):
        """
        Add a starter to set when the stop mechanism is set
        """
        self.starters.append(starter)

    def add_backup(self, backup):
        """
        Add a backup to start when the stop mechanism is set
        """
        if backup and backup not in self.backup_list:
            self.backup_list.append(backup)

    def add_child(self, child):
        """
        Add a child to propagate stop signals to
        """
        self.children.append(child)

    def is_set(self):
        """
        Test if the stop mechanism is set
        """
        return self.is_alive()

    def set(self):
        """
        Start the stop mechanism if it is enabled,
        propagate to children otherwise
        """
        if self.enable_flag and not self.is_alive():
            self.start()
        elif not self.enable_flag:
            for child in self.children:
                child.set()

    def run(self):
        """
        Run the stop mechanism
        """
        # Logging
        LOGGER.info(None, extra=self.log_dict)
        # Set all the starters
        for starter in self.starters:
            starter.set()
        # Wait for the execution to finish
        self.main_thread.runable_sequence_finished.wait()
        # No backup case
        if not self.backup_list:
            return
        # Sort the backup list
        key = lambda x: getattr(getattr(x, 'xml_sequence'), 'level')
        backup_list = list(reversed(sorted(self.backup_list, key=key)))
        # Link the backup executions
        first_backup = prev_backup = backup_list[0]
        for backup in backup_list[1:]:
            prev_backup.next_execution = backup
            prev_backup = backup
        # Run backup
        first_backup.start()
        # Wait for backup to finish
        for backup in backup_list:
            backup.join()


# Root Sequence Thread
class RootSequenceThread(Thread):
    """
    Class to implement the root sequence and run it in a thread
    """

    def __init__(self, xml_sequence, stop_thread_parent=None):
        """
        Initialize the root sequence thread
        """
        Thread.__init__(self)
        # Init attributes
        self.xml_sequence = xml_sequence
        self.backup_root_threads = []
        self.next_execution = None
        # Stop thread
        self.stop_thread = StopThread(self)
        if stop_thread_parent:
            stop_thread_parent.add_child(self.stop_thread)
        # Create the sequence
        self.runable_sequence_finished = Event()
        self.runable_sequence = RunableSequence(xml_sequence,
                                                self.stop_thread, root=True)

    def run(self):
        """
        Run the root sequence
        """
        # Run the runable sequence
        self.stop_thread.enable()
        self.runable_sequence.run()
        self.stop_thread.disable()
        # Wait for the stop mecanism to finish
        self.runable_sequence_finished.set()
        if self.stop_thread.is_alive():
            self.stop_thread.join()
        # Launch the next execution
        if self.next_execution:
            self.next_execution.start()

    def stop(self):
        """
        Stop the current sequence execution.
        Note that it is not necessarily the "self" instance.
        """
        self.stop_thread.set()
