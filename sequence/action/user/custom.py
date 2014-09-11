from sequence import AbstractAction

PARAMETERS = """
param_1 : default_string : unicode
param_2 : 3.141592653589 : float
param_3 : 42 : int
param_4 : small: small, big, HUGE
"""

class MyCustomAction(AbstractAction):

    def pre_run(self):
        self.it = iter(enumerate([self.param_1, self.param_2,
                                  self.param_3, self.param_4]))
        return True

    def run(self):
        msg = "Parameter {} = {}".format(*next(self.it))
        self.info(msg)
        return True

    def post_run(self):
        return self.all_ok()
