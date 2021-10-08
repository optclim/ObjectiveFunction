__all__ = ['ObjectiveFunctionMisfit']

import random

from .objective_function import ObjectiveFunction


class ObjectiveFunctionMisfit(ObjectiveFunction):
    """class maintaining a lookup table for an objective function

    store the model misfit in the database

    :param basedir: the directory in which the lookup table is kept
    :type basedir: Path
    :param parameters: a dictionary mapping parameter names to the range of
        permissible parameter values
    """

    RESULT_TYPE = "float"

    def _get_result(self, result=None):
        """get result from information stored in lookup table

        :param result: the result value stored in the lookup table or None
                       when the result is not yet known
        """

        if result is None:
            return random.random()
        else:
            return result

    def _set_result(self, pid, result):
        """convert result to value to be stored in lookup table

        :param result: result as computed by real objective function
        :param pid: parameter set ID
        :return: value to be stored in lookup table"""

        return float(result)
