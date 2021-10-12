__all__ = ['ObjectiveFunctionResidual']

import numpy.random
import numpy
from typing import Mapping
from pathlib import Path

from .parameter import Parameter
from .objective_function import ObjectiveFunction, LookupState


class ObjectiveFunctionResidual(ObjectiveFunction):
    """class maintaining a lookup table for an objective function

    store the name of a file containing the residuals

    :param basedir: the directory in which the lookup table is kept
    :type basedir: Path
    :param parameters: a dictionary mapping parameter names to the range of
        permissible parameter values
    """

    RESULT_TYPE = "text"

    def __init__(self, basedir: Path,                   # noqa: C901
                 parameters: Mapping[str, Parameter]):
        """constructor"""

        super().__init__(basedir, parameters)

        self._num_residuals = None

    @property
    def num_residuals(self):
        """the number of residuals"""
        if self._num_residuals is None:
            return 50
        else:
            return self._num_residuals

    def get_result(self, params):
        """look up parameters

        :param parms: dictionary containing parameter values
        :raises OptClimNewRun: when lookup fails
        :raises OptClimWaiting: when completed entries are required
        :return: returns the value if lookup succeeds and state is completed
                 return a random value otherwise
        :rtype: numpy.arraynd
        """

        result = self._lookup_params(params)

        if result is None:
            return numpy.random.rand(self.num_residuals)
        else:
            with open(result, 'rb') as f:
                result = numpy.load(f)
            if self._num_residuals is None:
                self._num_residuals = result.size
            return result

    def set_result(self, params, result):
        """set the result for a paricular parameter set

        :param parms: dictionary of parameters
        :param result: residuals to store
        :type result: numpy.ndarray
        """

        pid = self._set_result_prepare(params)
        # store residuals in file
        fname = self.basedir / f'residuals_{pid}.npy'
        with open(fname, 'wb') as f:
            numpy.save(f, result)

        # update lookup table
        cur = self.con.cursor()
        cur.execute('update lookup set state = ?, result = ? where id = ?;',
                    (LookupState.COMPLETED.value, str(fname), pid))
        self.con.commit()
