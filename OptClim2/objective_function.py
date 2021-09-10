__all__ = ['OptClimNewRun', 'ObjectiveFunction']

import logging
from typing import Mapping
import sqlite3
from pathlib import Path
import random

from .parameter import Parameter


class OptClimNewRun(Exception):
    pass


class ObjectiveFunction:
    """class maintaining a lookup table for an objective function

    the state of a parameter set can be on of
     * n - new
     * a - active
     * c - completed

    :param basedir: the directory in which the lookup table is kept
    :type basedir: Path
    :param parameters: a dictionary mapping parameter names to the range of
        permissible parameter values
    """

    def __init__(self, basedir: Path,                   # noqa: C901
                 parameters: Mapping[str, Parameter]):
        """constructor"""

        if len(parameters) == 0:
            raise RuntimeError('no parameters given')

        self._parameters = parameters
        self._log = logging.getLogger('OptClim2.ObjectiveFunction')

        dbName = basedir / 'objective_function.sqlite'

        # generate database query strings
        self._paramlist = tuple(sorted(list(parameters.keys())))
        slct = []
        insrt = []
        for p in self._paramlist:
            # make sure that parameter names are alpha numeric to avoid
            # sql injection attacks
            if not p.isalnum():
                raise ValueError(f'{p} should be alpha-numeric')
            slct.append(f'{p}=:{p}')
            insrt.append(f':{p}')
        insrt.append('"n"')
        insrt.append('null')
        self._select_new_str = ', '.join(self._paramlist)
        self._select_str = ' and '.join(slct)
        self._insert_str = '(null,' + ','.join(insrt) + ')'

        if not dbName.exists():
            self._log.info('create db')
            self._con = sqlite3.connect(dbName)

            cur = self.con.cursor()
            cur.execute(
                """create table if not exists parameters
                (name text, minv real, maxv real, resolution real);
                """)
            cols = []
            for p in self._paramlist:
                cols.append(f'{p} integer')
                cur.execute("insert into parameters values (?,?,?,?);",
                            (p, parameters[p].minv, parameters[p].maxv,
                             parameters[p].resolution))
            cols.append("state text")
            cols.append("result float")
            cur.execute(
                "create table if not exists lookup ("
                "id integer primary key autoincrement, "
                "{0});".format(",".join(cols)))
            self.con.commit()
        else:
            self._log.info('checking db')
            self._con = sqlite3.connect(dbName)
            paramlist = list(parameters.keys())

            cur = self.con.cursor()
            cur.execute('select * from parameters;')
            error = False
            for p, minv, maxv, res in cur.fetchall():
                if p not in paramlist:
                    self._log.error(
                        f'parameter {p} not found in configuration')
                    error = True
                    continue
                if abs(res - parameters[p].resolution) > min(
                        res, parameters[p].resolution):
                    self._log.error(f'resolution of {p} does not match')
                    error = True
                if abs(minv - parameters[p].minv) > parameters[p].resolution:
                    self._log.error(f'min value of {p} does not match')
                    error = True
                if abs(maxv - parameters[p].maxv) > parameters[p].resolution:
                    self._log.error(f'max value of {p} does not match')
                    error = True
                paramlist.remove(p)
            for p in paramlist:
                self._log.error(f'parameter {p} not found in database')
                error = True
            if error:
                raise RuntimeError('configuration does not match database')

    @property
    def con(self):
        return self._con

    @property
    def parameters(self):
        return self._parameters

    def _values2params(self, values):
        """create a dictionary of parameter values from list of values

        :param values: a list/tuple of values
        :return: a dictionary of parameters
        """
        assert len(values) == len(self._paramlist)
        params = {}
        for i, p in enumerate(self._paramlist):
            params[p] = values[i]
        return params

    def _getIparam(self, params):
        """convert dictionary of real valued parameters to scaled integer
        parameters"""
        if len(params) != len(self.parameters):
            raise RuntimeError("the number of parameters does not match")
        iparam = {}
        for p in params:
            if p not in self.parameters:
                raise RuntimeError(f'parameter {p} not found')
            iparam[p] = self.parameters[p].value2int(params[p])
        return iparam

    def _getRparam(self, params):
        """convert dictionary of integer valued parameters to real
           parameters"""
        if len(params) != len(self.parameters):
            raise RuntimeError("the number of parameters does not match")
        rparam = {}
        for p in params:
            if p not in self.parameters:
                raise RuntimeError(f'parameter {p} not found')
            rparam[p] = self.parameters[p].int2value(params[p])
        return rparam

    def state(self, params):
        """look up parameters

        :param parms: dictionary containing parameter values
        :raises LookupError: if entry for parameter set does not exist
        :return: string containing state
        """
        iparam = self._getIparam(params)
        cur = self.con.cursor()
        cur.execute(
            'select state from lookup where ' + self._select_str,
            iparam)
        r = cur.fetchone()
        if r is None:
            raise LookupError("no entry for parameter set found")
        return r[0]

    def __call__(self, params):
        """look up parameters

        :param parms: dictionary containing parameter values
        :raises OptClimNewRun: when lookup fails
        :return: returns the value if lookup succeeds and state is completed
                 return a random value otherwise
        """
        iparam = self._getIparam(params)
        cur = self.con.cursor()
        cur.execute(
            'select state, result from lookup where ' + self._select_str,
            iparam)
        r = cur.fetchone()
        if r is None:
            cur.execute(
                'insert into lookup values ' + self._insert_str,
                iparam)
            self.con.commit()

            raise OptClimNewRun()

        if r[0] == 'c':
            return r[1]
        else:
            return random.random()

    def get_new(self):
        """get a set of parameters that are not yet processed

        The parameter set changes set from new to active

        :return: dictionary of parameter values for which to compute the model
        :raises RuntimeError: if there is no new parameter set
        """
        cur = self.con.cursor()
        cur.execute(
            'select id,' + self._select_new_str + ' from lookup '
            'where state = "n";')
        r = cur.fetchone()
        if r is None:
            raise RuntimeError('no new parameter sets')

        param = self._values2params(r[1:])
        pid = r[0]

        cur.execute('update lookup set state = ? where id = ?;', ('a', pid))
        self.con.commit()

        return self._getRparam(param)

    def set_result(self, params, result):
        """set the result for a paricular parameter set

        :param parms: dictionary of parameters
        :param result: result value to set
        :type result: float
        :raises LookupError: if entry for parameter set does not exist
        :raises RuntimeError: if the parameter set is not in active state
        """
        iparam = self._getIparam(params)
        cur = self.con.cursor()
        cur.execute(
            'select id, state from lookup where ' + self._select_str,
            iparam)
        r = cur.fetchone()
        if r is None:
            raise LookupError("no entry for parameter set found")
        pid, state = r

        if state != 'a':
            raise RuntimeError(f'parameter set is in wrong state {state}')

        cur.execute('update lookup set state = ?, result = ? where id = ?;',
                    ('c', float(result), pid))
        self.con.commit()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    params = {'a': Parameter(1, 2), 'b': Parameter(-1, 1)}
    objFun = ObjectiveFunction(Path('/tmp'), params)

    print(objFun({'a': 1, 'b': 0}))
