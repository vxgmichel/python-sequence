# -*- coding: utf-8 -*-

import PyTango
import __builtin__
from time import clock, sleep
from sequence import AbstractAction

PARAMETERS = """
device_name : family/domain/member : str
command : command : str
arg_enabled : False : bool
arg_value : value : unicode
arg_type : str : str, unicode, bool, int, float
start_state : STANDBY : ANY, ON, OFF, CLOSE, OPEN, INSERT, EXTRACT, MOVING, STANDBY, FAULT, INIT, RUNNING, ALARM, DISABLE, UNKNOWN
stop_state : STANDBY : ANY, ON, OFF, CLOSE, OPEN, INSERT, EXTRACT, MOVING, STANDBY, FAULT, INIT, RUNNING, ALARM, DISABLE, UNKNOWN
timeout : 15.0 : float
"""

class CommandeTango(AbstractAction):

    def pre_run(self):
        if self.arg_enabled:
            # Test le paramètre 'arg_type'
            try:
                self.arg_type = getattr(__builtin__, self.arg_type)
            except AttributeError as e:
                self.error(e)
                msg = u"Le paramètre 'arg_type' n'est pas un type valide"
                self.error(msg)
                return False
            # Test le paramètre 'arg_value'
            try:
                self.arg_value = self.arg_type(self.arg_value)
            except :
                msg = u"Le paramètre 'arg_value' n'est pas valide"
                self.error(msg)
                return False
        # Test le paramètre 'start_state'
        if self.start_state != "ANY":
            try:
                self.start_state = getattr(PyTango.DevState, self.start_state)
            except AttributeError:
                msg = u"Le paramètre 'start_state' n'est pas un état valide"
                self.error(msg)
                return False
        # Test le paramètre 'stop_state'
        if self.stop_state != "ANY":
            try:
                self.stop_state = getattr(PyTango.DevState, self.stop_state)
            except AttributeError:
                msg = u"Le paramètre 'stop_state' n'est pas un état valide"
                self.error(msg)
                return False
        # Test le paramètre 'timeout'
        if self.timeout < 0:
            msg = u"La valeur du paramètre 'timeout' doit être supérieur à 0"
            self.error(msg)
            return False
        # Test le paramètre 'device_name'
        self.device = PyTango.DeviceProxy(self.device_name)
        if self.start_state != "ANY" and self.device.State() != self.start_state:
            msg = u"L'état du device server doit être l'état de départ"
            self.error(msg)
            return False
        try:
            self.command = getattr(self.device, self.command)
        except AttributeError:
            msg = u"Le paramètre 'command' n'est pas une commande valide"
            self.error(msg)
            return False
        return True
            

    def run(self):
        # Test l'état de départ
        if self.start_state != "ANY" and self.device.State() != self.start_state:
            msg = u"L'état du device server doit être l'état de départ"
            self.error(msg)
            return False
        # Send command
        if self.arg_enabled:
            res = self.command(self.arg_value)
        else:
            res = self.command()
        self.info(u"La commande a retourné : {}".format(res))
        # Init Loop
        delta = 0
        is_done = (self.device.State() == self.stop_state)
        time_ref = clock()
        # Loop
        while delta < self.timeout and not is_done:
            sleep(0.5)
            is_done = (self.device.State() == self.stop_state or self.stop_state == "ANY")
            delta = clock()-time_ref
        if not is_done:
            msg = u"Le timeout a expiré"
            self.error(msg)
            return False
        msg = u"L'état de fin a été atteint"
        self.info(msg)
        return True

    def post_run(self):
        return self.all_ok() and (self.device.State() == self.stop_state) 
