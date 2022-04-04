__all__ = ['PreliminaryRun', 'NewRun', 'Waiting', 'NoNewRun',
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


class NoNewRun(Exception):
    """Exception used to indicate that no new runs to be computed"""
    pass


class LookupState(Enum):
    """the state of the parameter set

     * PROVISIONAL: new entry under consideration
     * NEW: new parameter set
     * CONFIGURING: the model run is being configured
     * CONFIGURED: the model run has been configured
     * ACTIVE: parameter set being computed
     * RUN: the model has run
     * POSTPROCESSING: the model results are being post-processed
     * COMPLETED: completed parameter set
    """
    PROVISIONAL = 1
    NEW = 2
    CONFIGURING = 3
    CONFIGURED = 4
    ACTIVE = 5
    RUN = 6
    POSTPROCESSING = 7
    COMPLETED = 8
