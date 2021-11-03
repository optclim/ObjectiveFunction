__all__ = ['OptClimPreliminaryRun', 'OptClimNewRun', 'OptClimWaiting',
           'LookupState', 'ObjectiveFunction']

import logging
from typing import Mapping
import sqlite3
from pathlib import Path
from enum import Enum
import numpy
from abc import ABCMeta, abstractmethod

from .parameter import Parameter


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


class ObjectiveFunction(metaclass=ABCMeta):
    """class maintaining a lookup table for an objective function

    :param basedir: the directory in which the lookup table is kept
    :type basedir: Path
    :param parameters: a dictionary mapping parameter names to the range of
        permissible parameter values
    """

    RESULT_TYPE = None

    def __init__(self, basedir: Path,                   # noqa: C901
                 parameters: Mapping[str, Parameter]):
        """constructor"""

        if len(parameters) == 0:
            raise RuntimeError('no parameters given')

        self._parameters = parameters
        self._log = logging.getLogger(f'OptClim2.{self.__class__.__name__}')
        self._basedir = basedir

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
        insrt.append(str(LookupState.PROVISIONAL.value))
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
            cols.append("state integer")
            if self.RESULT_TYPE is not None:
                cols.append(f"result {self.RESULT_TYPE}")
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

        self._lb = None
        self._ub = None

    @property
    def basedir(self):
        """the basedirectory"""
        return self._basedir

    @property
    def con(self):
        return self._con

    @property
    def num_params(self):
        """the number of parameters"""
        return len(self._parameters)

    @property
    def parameters(self):
        """dictionary of parameters"""
        return self._parameters

    @property
    def lower_bounds(self):
        """an array containing the lower bounds"""
        if self._lb is None:
            self._lb = []
            for p in self._paramlist:
                self._lb.append(self.parameters[p].minv)
            self._lb = numpy.array(self._lb)
        return self._lb

    @property
    def upper_bounds(self):
        """an array containing the upper bounds"""
        if self._ub is None:
            self._ub = []
            for p in self._paramlist:
                self._ub.append(self.parameters[p].maxv)
            self._ub = numpy.array(self._ub)
        return self._ub

    def values2params(self, values):
        """create a dictionary of parameter values from list of values

        :param values: a list/tuple of values
        :return: a dictionary of parameters
        """
        assert len(values) == len(self._paramlist)
        params = {}
        for i, p in enumerate(self._paramlist):
            params[p] = values[i]
        return params

    def params2values(self, params):
        """create an array of values from a dictionary of parameters

        :param params: a dictionary of parameters
        :return: a array of values
        """
        values = []
        for p in self._paramlist:
            values.append(params[p])
        return numpy.array(values)

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
        :return: state
        :rtype: LookupState
        """
        iparam = self._getIparam(params)
        cur = self.con.cursor()
        cur.execute(
            'select state from lookup where ' + self._select_str,
            iparam)
        r = cur.fetchone()
        if r is None:
            raise LookupError("no entry for parameter set found")
        return LookupState(r[0])

    def __call__(self, x, grad):
        """look up parameters

        :param x: vector containing parameter values
        :param grad: vector of length 0
        :type grad: numpy.ndarray
        :raises OptClimNewRun: when lookup fails
        :raises OptClimWaiting: when completed entries are required
        :return: returns the value if lookup succeeds and state is completed
                 return a random value otherwise
        :rtype: float
        """
        if grad.size > 0:
            raise RuntimeError(
                'OptClim2 only supports derivative free optimisations')
        return self.get_result(self.values2params(x))

    def _lookup_params(self, params):
        """look up parameters

        :param parms: dictionary containing parameter values
        :raises OptClimNewRun: when lookup fails
        :raises OptClimWaiting: when completed entries are required
        :return: returns the value of the lookup
        """
        iparam = self._getIparam(params)
        self._log.debug('looking up params')
        cur = self.con.cursor()
        cur.execute(
            'select state, id, result from lookup where ' + self._select_str,
            iparam)
        r = cur.fetchone()
        if r is None:
            # check if we already have a provisional value
            cur.execute('select id from lookup where state = ?;',
                        (LookupState.PROVISIONAL.value,))
            r = cur.fetchone()
            if r is None:
                self._log.info('new provisional parameter set')
                # a provisional value
                cur.execute(
                    'insert into lookup values ' + self._insert_str,
                    iparam)
                self.con.commit()
                raise OptClimPreliminaryRun
            else:
                # we already have a provisional value
                # delete the previous one and wait
                self._log.info('remove provisional parameter set')
                cur.execute(
                    'delete from lookup where id = ?;', (r[0], ))
                self.con.commit()
                raise OptClimWaiting

        state = LookupState(r[0])
        if state == LookupState.PROVISIONAL:
            self._log.info('provisional parameter set changed to new')
            cur.execute('update lookup set state = ? where id = ?;',
                        (LookupState.NEW.value, r[1]))
            self.con.commit()
            raise OptClimNewRun
        elif state == LookupState.COMPLETED:
            self._log.debug('hit completed parameter set')
        else:
            self._log.debug('hit new/active parameter set')
        return r[2]

    @abstractmethod
    def get_result(self, params):
        """look up parameters

        :param parms: dictionary containing parameter values
        :raises OptClimNewRun: when lookup fails
        :raises OptClimWaiting: when completed entries are required
        :return: returns the value if lookup succeeds and state is completed
                 return a random value otherwise
        :rtype: float
        """
        pass

    def get_new(self):
        """get a set of parameters that are not yet processed

        The parameter set changes set from new to active

        :return: dictionary of parameter values for which to compute the model
        :raises RuntimeError: if there is no new parameter set
        """
        cur = self.con.cursor()
        cur.execute('update lookup set state = ? where id in '
                    '(select id from lookup where state = ? limit 1)'
                    ' returning ' + self._select_new_str,
                    (LookupState.ACTIVE.value, LookupState.NEW.value))

        r = cur.fetchone()
        if r is None:
            raise RuntimeError('no new parameter sets')

        param = self.values2params(r)
        self.con.commit()

        return self._getRparam(param)

    def _set_result_prepare(self, params):
        """check state of lookup table and prepare for setting result

        :param parms: dictionary of parameters
        :return: parameter set ID
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

        if LookupState(state) != LookupState.ACTIVE:
            raise RuntimeError(f'parameter set is in wrong state {state}')

        return pid

    @abstractmethod
    def set_result(self, params, result):
        pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    params = {'a': Parameter(1, 2), 'b': Parameter(-1, 1)}
    objFun = ObjectiveFunction(Path('/tmp'), params)

    print(objFun({'a': 1, 'b': 0}))
