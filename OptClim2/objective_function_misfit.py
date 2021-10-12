__all__ = ['ObjectiveFunctionMisfit']

import random

from .objective_function import ObjectiveFunction, LookupState


class ObjectiveFunctionMisfit(ObjectiveFunction):
    """class maintaining a lookup table for an objective function

    store the model misfit in the database

    :param basedir: the directory in which the lookup table is kept
    :type basedir: Path
    :param parameters: a dictionary mapping parameter names to the range of
        permissible parameter values
    """

    RESULT_TYPE = "float"

    def get_result(self, params):
        """look up parameters

        :param parms: dictionary containing parameter values
        :raises OptClimNewRun: when lookup fails
        :raises OptClimWaiting: when completed entries are required
        :return: returns the value if lookup succeeds and state is completed
                 return a random value otherwise
        :rtype: float
        """
        result = self._lookup_params(params)

        if result is None:
            return random.random()
        else:
            return result

    def set_result(self, params, result):
        """set the result for a paricular parameter set

        :param parms: dictionary of parameters
        :param result: result value to set
        :type result: float
        """

        pid = self._set_result_prepare(params)

        # update lookup table
        cur = self.con.cursor()
        cur.execute('update lookup set state = ?, result = ? where id = ?;',
                    (LookupState.COMPLETED.value, float(result), pid))
        self.con.commit()
