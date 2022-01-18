__all__ = ['ObjectiveFunctionMisfit']

import random

from .objective_function import ObjectiveFunction, LookupState
from .model import DBRunMisfit


class ObjectiveFunctionMisfit(ObjectiveFunction):
    """class maintaining a lookup table for an objective function

    store the model misfit in the database

    :param study: the name of the study
    :type study: str
    :param basedir: the directory in which the lookup table is kept
    :type basedir: Path
    :param parameters: a dictionary mapping parameter names to the range of
        permissible parameter values
    :param simulation: name of the default simulation
    :type simulation: str
    :param db: database connection string
    :type db: str
    """

    _Run = DBRunMisfit

    def get_result(self, params, simulation=None):
        """look up parameters

        :param parms: dictionary containing parameter values
        :param simulation: the name of the simulation
        :raises OptClimNewRun: when lookup fails
        :raises OptClimWaiting: when completed entries are required
        :return: returns the value if lookup succeeds and state is completed
                 return a random value otherwise
        :rtype: float
        """

        run = self._lookupRun(params, simulation=simulation)
        if run.state != LookupState.COMPLETED:
            return random.random()
        else:
            return run.misfit

    def set_result(self, params, result, simulation=None):
        """set the result for a paricular parameter set

        :param parms: dictionary of parameters
        :param result: result value to set
        :param simulation: the name of the simulation
        :type result: float
        """

        run = self._getRun(params, simulation=simulation)
        if run.state == LookupState.ACTIVE:
            run.state = LookupState.COMPLETED
            run.misfit = result
            self.session.commit()
        else:
            raise RuntimeError(f'parameter set is in wrong state {run.state}')
