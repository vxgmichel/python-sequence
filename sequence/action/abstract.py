# -*- coding: utf-8 -*-

""" Module for executing actions """

# ------------------------------------------------------------------------------
# Name:        Actions
# Purpose:
#
# Author:      michel.vincent
#
# Created:     09/10/2013
# Copyright:   (c) michel.vincent 2013
# Licence:     GPL
# ------------------------------------------------------------------------------


# Imports
from pkgutil import walk_packages
from collections import OrderedDict as ODict
from importlib import import_module
from time import sleep
import __builtin__


# Imports from constants
from sequence.common.constant import LOGGER
from sequence import action as action_package
from sequence.action import user as user_action_package


# Patch actions package
def patch_action_package(arg):
    """
    Patch the actions with a path or a list of path.
    """
    if isinstance(arg, basestring):
        user_action_package.__path__.append(arg)
    else:
        user_action_package.__path__.extend(arg)


# Get action list
def get_action_list():
    """
    Get the list of available actions
    """
    result = []
    path = action_package.__path__
    prefix = action_package.__name__ + "."
    for _, module_name, _ in walk_packages(path, prefix):
        try:
            module = import_module(module_name)
        except Exception:
            pass
        else:
            action_class = get_action_from_module(module)
            if action_class:
                result.append((action_class.__name__, module_name))
    return sorted(result)


# Get action from module
def get_action_from_module(module):
    """
    Import a module to get the action class.
    """
    for key in dir(module):
        attr = getattr(module, key)
        if isinstance(attr, type) and \
           issubclass(attr, AbstractAction) and \
           attr is not AbstractAction:
            return attr
    return None


# Process a module
def process_module(module_name, with_parameters=True):
    """
    Process a module to get the action class and default parameters
    """
    # Import action module
    try:
        module = import_module(module_name)
    except Exception as exc:
        raise ActionCreationError(repr(exc))
    # Get action class
    action_class = get_action_from_module(module)
    if not action_class:
        msg = "Action class '{}' not found"
        msg = msg.format(module_name)
        raise ActionCreationError(msg)
    # Parse parameters
    parameters_string = getattr(module, "PARAMETERS", None)
    if with_parameters and parameters_string:
        try:
            default_parameters = parse_default_parameters(parameters_string)
        except Exception as e:
            msg = str("Error while parsing parameters of action module '{}'"
                      .format(e))
            msg = msg.format(module_name)
            raise ActionCreationError(msg)
    else:
        default_parameters = {}
    return action_class, default_parameters


# Create action definition
def create_action(xml_block):
    """
    Create an action from an xml block
    """
    # Get data
    name = xml_block.block_id
    module_name = xml_block.properties.module
    iteration = xml_block.properties.iteration
    tick = xml_block.properties.tick
    # Process the module
    action_class, default_parameters = process_module(module_name)
    if default_parameters:
        action_class.set_default_parameters(default_parameters)
    parameters = cast_parameters(xml_block, default_parameters)
    # Create action
    action = action_class(name, module_name, iteration, tick, parameters)
    return action


def cast_parameters(xml_block, default_parameters):
    """
    Cast parameters of an xml block with the default parameters
    """
    result = ODict(default_parameters)
    for name, value in xml_block.parameters.items():
            if name not in default_parameters:
                msg = "Action '{}' has no parameters called '{}'"
                msg = msg.format(xml_block.block_id, name)
                raise ActionCreationError(msg)
            try:
                if isinstance(default_parameters[name], bool) and \
                   isinstance(value, basestring):
                    if value.lower() in ["true", "1"]:
                        cast_value = True
                    elif value.lower() in ["false", "0"]:
                        cast_value = False
                    else:
                        raise Exception()
                else:
                    cast_value = type(default_parameters[name])(value)
            except:
                msg = "Error while casting parameters '{}' of action '{}'"
                msg = msg.format(name, xml_block.block_id)
                raise ActionCreationError(msg)
            result[name] = cast_value
    # Save values
    xml_block.parameters = ODict(result)
    # Cast Enum to string
    for name, value in result.items():
        if isinstance(value, BaseEnum):
            result[name] = unicode(value)
    return result


def parse_value(value, vtype):
    """
    Return a value for two strings (value and type)
    """
    if ',' in vtype:
        return enum_type(*vtype.split(","))(value)
    if vtype.lower() == 'bool':
        if value.lower() not in ['true', '1', 'false', '0']:
            raise TypeError('{} is not a valid bool'.format(value))
        return value.lower() in ['true', '1']
    return getattr(__builtin__, vtype.lower())(value)


def parse_line(line):
    """
    Return a (name, value) tuple from a parameter line.
    """
    name, value, vtype = (e.strip() for e in line.split(':'))
    return name, parse_value(value, vtype)


def parse_default_parameters(parameters):
    """
    Return a dictionnary from the default parameters string
    """
    return ODict(parse_line(line) for line in parameters.split("\n") if line)


# BaseEnum class definiton
class BaseEnum(unicode):
    """ Base class for enumerations in action parameters """
    pass


# Create enumerations in action parameters
def enum_type(*args):
    """
    Create an enumeration from string arguments
    """
    # Test args
    for arg in args:
        if not isinstance(arg, basestring):
            msg = "{} is not a string".format(arg)
            raise TypeError(msg)

    # Format strings
    values = [arg.strip() for arg in args]

    # Create MetaEnum
    values_property = property(lambda cls: values)
    MetaEnum = type("MetaEnum", (type,), {"values": values_property})

    # __new__ method
    def __new__(cls, value):
        if value not in cls.values:
            msg = "'{}' not in {}".format(value, cls.values)
            raise AttributeError(msg)
        return BaseEnum.__new__(cls, value)

    # __repr__ method
    def __repr__(self):
        return u"Element '{}' of Enum({})".format(unicode(self), self.values)

    # method dictionnary
    method_dict = {"__new__": __new__,
                   "__repr__": __repr__,
                   "values": property(lambda self: self.__class__.values)}

    # Create EnumType
    return MetaEnum("EnumType", (BaseEnum,), method_dict)


# Abstract action class definition
class AbstractAction(object):
    """
    Class providing a basis for action creation and execution
    """

    _default_parameters = {}

    @classmethod
    def set_default_parameters(cls, params):
        """
        Class method to update default parameters
        """
        if hasattr(cls, '_parsed') and cls._parsed:
            return
        cls._parsed = True
        cls._default_parameters = params
        for name, value in params.items():
            if hasattr(cls, name):
                msg = "Class '{}' already has an attribute called '{}'"
                msg = msg.format(cls.__name__, name)
                raise ActionCreationError(msg)
            setattr(cls, name, value)

    def __init__(self, name, module, iteration, tick, parameters):
        """
        Initialize action
        """
        # Set properties
        self._log_dict = None
        self._name = name
        self._module = module
        self._iteration = iteration
        self._tick = tick
        self._parameters = parameters
        # Set flags
        self._valid_pre_run_flag = False
        self._valid_run_count = 0
        # Set parameters
        for name, value in parameters.items():
            setattr(self, name, value)

    def execute(self, stop_thread, log_dict):
        """
        Execute action and log it with the stop mecanism and logging dictionary
        """
        self._log_dict = log_dict
        self._stop_thread = stop_thread
        # Stop thread activated case
        if self._stop_thread.is_set():
            self.warning('The stop mecanism has been activated before Pre_run')
            return False
        # Try PreRun
        try:
            self.info('PreRun')
            self._valid_pre_run_flag = self.pre_run()
        except Exception as exc:
            self.error('PreRun failed:')
            self.error(repr(exc))
        # Warning if PreRun returned False
        if not self._valid_pre_run_flag:
            self.warning('PreRun returned False')
        # Stop thread activated case
        elif self._stop_thread.is_set():
            self.warning('The stop mecanism has been activated during PreRun')
        # If PreRun returned True
        elif self._valid_pre_run_flag:
            # Log info
            if self._iteration == 1:
                self.info('Run')
            else:
                self.info('Run ({} iterations)'.format(self._iteration))
            # Run Loop
            for i in range(self._iteration):
                # Try Run
                try:
                    run_result = self.run()
                except Exception as exc:
                    self.error('Run failed on execution {}:'.format(i+1))
                    self.error(repr(exc))
                    break
                # Break if Run returned False
                if not run_result:
                    msg = 'Run returned False on execution {}'.format(i+1)
                    self.warning(msg)
                    break
                # Break if stop thread activated
                if self._stop_thread.is_set() and i != self._iteration-1:
                    msg = 'The stop mecanism has been activated during Run'
                    msg += ' (execution {})'.format(i+1)
                    self.warning(msg)
                    break
                # Sleep
                self._valid_run_count += 1
                sleep(self._tick)
                # Break if stop thread activated
                if self._stop_thread.is_set() and i != self._iteration-1:
                    msg = 'The stop mecanism has been activated during Run'
                    msg += ' (tick {})'.format(i+1)
                    self.warning(msg)
                    break
        # Try Post run
        try:
            self.info('PostRun')
            result = self.post_run()
        except Exception as exc:
            self.error('PostRun failed:')
            self.error(repr(exc))
            return False
        # Error if PostRun returned False
        if not result:
            self.warning('PostRun returned False')
        # Return result
        return result

    # Methods to override
    def pre_run(self):
        """ Pre-run execution """
        return True

    def run(self):
        """ Run execution """
        return True

    def post_run(self):
        """ Post-run execution """
        return self.all_ok()

    # Test methods
    def all_ok(self):
        """ Return True if everything went good """
        return self._valid_run_count == self._iteration

    def pre_run_ok(self):
        """ Return True if pre-run went good """
        return self._valid_pre_run_flag

    # Logging methods
    def debug(self, msg):
        """ Logging method with debug level """
        LOGGER.debug(msg, extra=self._log_dict)

    def info(self, msg):
        """ Logging method with info level """
        LOGGER.info(msg, extra=self._log_dict)

    def warning(self, msg):
        """ Logging method with warning level """
        LOGGER.warning(msg, extra=self._log_dict)

    def error(self, msg):
        """ Logging method with error level """
        LOGGER.error(msg, extra=self._log_dict)

    def critical(self, msg):
        """ Logging method with critical level """
        LOGGER.critical(msg, extra=self._log_dict)


# Action Creation Error class definition
class ActionCreationError(StandardError):
    """ Custom error raised when an action creation error is detected """

    def __init__(self, strerror):
        StandardError.__init__(self, strerror)
        self.strerror = strerror

    def __str__(self):
        return self.strerror
