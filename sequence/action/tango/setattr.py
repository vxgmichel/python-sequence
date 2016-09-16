# -*- coding: utf-8 -*-

import PyTango
from sequence import AbstractAction

PARAMETERS = """
device_name : domain/family/member : str
attr_name : attrname : str
type : str : str,int,bool,float
value : val : str
"""

class SetTangoAttr(AbstractAction):
    """
    Used to set the value of a Tango attribute
    """

    def pre_run(self):
        # Test le paramètre 'device_name'
        try:
            self.device = PyTango.DeviceProxy(self.device_name)
        except:
            msg = u"Device {} not defined in the database".format(self.device_name)
            self.error(msg)
            return False
        try:
            self.device.ping()
        except:
            msg = u"Device {} unreachable".format(self.device_name)
            self.error(msg)
            return False
            
            
        # Test le paramètre 'attr_name'
        if self.attr_name.lower() not in [name.lower() for name in self.device.get_attribute_list()]:
            msg = u"Device {} has no attribute {}".format(self.device_name, self.attr_name)
            self.error(msg)
            return False
        
        # Test le type et la valeur
        if self.type == 'int':
            try:
                self.casted_value = int(self.value)
            except:
                msg = u"Unable to cast {} to int".format(self.value)
                self.error(msg)
                return False
        elif self.type == 'str':
            try:
                self.casted_value = str(self.value)
            except:
                msg = u"Unable to cast {} to str".format(self.value)
                self.error(msg)
                return False
        elif self.type == 'float':
            try:
                self.casted_value = float(self.value)
            except:
                msg = u"Unable to cast {} to float".format(self.value)
                self.error(msg)
                return False
        elif self.type == 'bool':
            self.casted_value = self.value.lower() in ["1", "true", "vrai"]
            
        # Return
        return True

    def run(self):
        # Send command
        try:
            setattr(self.device, self.attr_name, self.casted_value)
        except:
            msg = u"Unable to set {} to {}".format(self.attr_name, self.casted_value)
            self.error(msg)
            return False
            
        msg = u"{} set to {}".format(self.attr_name, self.casted_value)
        self.info(msg)
        return True

    def post_run(self):
        return self.all_ok()
