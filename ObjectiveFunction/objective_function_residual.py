__all__ = ['ObjectiveFunctionResidual']

import numpy.random
import numpy
from typing import Mapping
from pathlib import Path

from .parameter import Parameter
from .objective_function import ObjectiveFunction, LookupState
from .model import DBRunPath


class ObjectiveFunctionResidual(ObjectiveFunction):
    """class maintaining a lookup table for an objective function

    store the name of a file containing the residuals

    :param study: the name of the study
    :type study: str
    :param basedir: the directory in which the lookup table is kept
    :type basedir: Path
    :param parameters: a dictionary mapping parameter names to the range of
        permissible parameter values
    :param scenario: name of the default scenario
    :type scenario: str
    :param db: database connection string
    :type db: str
    :param prelim: when True failed parameter look up raises a
                   PreliminaryRun exception otherwise a
                   NewRun exception is raised. Default=True
    :type prelim: bool
    """

    _Run = DBRunPath

    def __init__(self, study: str, basedir: Path,  # noqa C901
                 parameters: Mapping[str, Parameter],
                 scenario=None, db=None, prelim=True):
        """constructor"""

        super().__init__(study, basedir, parameters,
                         scenario=scenario, db=db, prelim=prelim)

        self._num_residuals = None

    @property
    def num_residuals(self):
        """the number of residuals"""
        if self._num_residuals is None:
            return 50
        else:
            return self._num_residuals

    def get_result(self, params, scenario=None):
        """look up parameters

        :param parms: dictionary containing parameter values
        :param scenario: the name of the scenario
        :raises NewRun: when lookup fails
        :raises Waiting: when completed entries are required
        :return: returns the value if lookup succeeds and state is completed
                 return a random value otherwise
        :rtype: numpy.arraynd
        """

        run = self._lookupRun(params, scenario=scenario)
        if run.state != LookupState.COMPLETED:
            return numpy.random.rand(self.num_residuals)
        else:
            with open(run.path, 'rb') as f:
                result = numpy.load(f)
            if self._num_residuals is None:
                self._num_residuals = result.size
            return result

    def set_result(self, params, result, scenario=None, force=False):
        """set the result for a paricular parameter set

        :param parms: dictionary of parameters
        :param result: residuals to store
        :param scenario: the name of the scenario
        :param force: force setting results irrespective of state
        :type result: numpy.ndarray
        """

        run = self._getRun(params, scenario=scenario)
        if run.state == LookupState.ACTIVE or force:
            # store residuals in file
            fname = self.basedir / f'residuals_{run.id}.npy'
            with open(fname, 'wb') as f:
                numpy.save(f, result)
            run.path = str(fname)
            run.state = LookupState.COMPLETED
            self.session.commit()
        else:
            raise RuntimeError(f'parameter set is in wrong state {run.state}')
