__all__ = ['ObjectiveFunctionResidual']

import numpy.random
import numpy
from typing import Mapping
from pathlib import Path

from .parameter import Parameter
from .objective_function import ObjectiveFunction


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

    def _get_result(self, result=None):
        """get result from information stored in lookup table

        :param result: the result value stored in the lookup table or None
                       when the result is not yet known
        """

        if result is None:
            return numpy.random.rand(self.num_residuals)
        else:
            with open(result, 'rb') as f:
                result = numpy.load(f)
            if self._num_residuals is None:
                self._num_residuals = result.size
            return result

    def _set_result(self, pid, result):
        """convert result to value to be stored in lookup table

        :param result: result as computed by real objective function
        :param pid: parameter set ID
        :return: value to be stored in lookup table"""

        fname = self.basedir / f'residuals_{pid}.npy'
        with open(fname, 'wb') as f:
            numpy.save(f, result)

        return str(fname)
