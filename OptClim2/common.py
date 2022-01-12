__all__ = ['OptClimPreliminaryRun', 'OptClimNewRun', 'OptClimWaiting',
           'LookupState']

from enum import Enum


class OptClimPreliminaryRun(Exception):
    """Exception used when a preliminary entry in the lookup
    table was created"""
    pass


class OptClimNewRun(Exception):
    """Exception used when a new entry in the lookup table was created"""
    pass


class OptClimWaiting(Exception):
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
