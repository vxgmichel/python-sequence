from sequence import AbstractAction

PARAMETERS = """
log_value : debug_string : unicode
return_false : False : bool
"""


class Debug(AbstractAction):

    def run(self):
        self.info(self.log_value)
        return True

    def post_run(self):
        return not self.return_false
