"""This package contains tools to create, edit and run action-based sequences."""

# Make script available at package level for -m execution
from sequence import script
__path__.extend(script.__path__)

# Raise up useful objects for user-defined actions
from sequence.action.abstract import AbstractAction, patch_action_package


