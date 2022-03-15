__all__ = ['PreliminaryRun', 'NewRun', 'Waiting',
           'LookupState']

from enum import Enum


class PreliminaryRun(Exception):
    """Exception used when a preliminary entry in the lookup
    table was created"""
    pass


class NewRun(Exception):
    """Exception used when a new entry in the lookup table was created"""
    pass


class Waiting(Exception):
    """Exception used to indicate that entries need to be completed"""
    pass


class LookupState(Enum):
    """the state of the parameter set

     * PROVISIONAL: new entry under consideration
     * NEW: new parameter set
     * ACTIVE: parameter set being computed
     * COMPLETED: completed parameter set
    """
    PROVISIONAL = 1
    NEW = 2
    ACTIVE = 3
    COMPLETED = 4
