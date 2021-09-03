__all__ = ['OptClimNewRun', 'Parameter', 'ObjectiveFunction']

import logging
from typing import Mapping
import sqlite3
from pathlib import Path
import random


class OptClimNewRun(Exception):
    pass


class Parameter:
    """a parameter with minimum and maximum value

    :param minv: minimum value (inclusive)
    :type minv: float
    :param maxv: maximum value (inclusive)
    :type maxv: flat
    :param resolution: resolution, by default 1e-6
    :type resolution: float
    """

    def __init__(self, minv: float, maxv: float,
                 resolution: float = 1e-6) -> None:
        """constructor"""

        self._minv = float(minv)
        self._maxv = float(maxv)
        self._resolution = float(resolution)
        if self.minv >= self.maxv:
            raise ValueError('minv must be smaller than maxv')

    def __repr__(self):
        return f'Parameter({self.minv}, {self.maxv}, ' \
            f'resolution={self.resolution})'

    @property
    def minv(self) -> float:
        """the minimum value the parameter can take"""
        return self._minv

    @property
    def maxv(self) -> float:
        """the maximum value the parameter can take"""
        return self._maxv

    @property
    def resolution(self) -> float:
        """the resolution used when converting between integer and floats"""
        return self._resolution

    def scale(self, value: float) -> float:
        """scale the value to the interval [0,1]

        :param value: value to be scaled
        :type value: float
        """
        if value < self.minv or value > self.maxv:
            raise ValueError(
                f'{value} outside parameter '
                'interval [{self.minv},{self.maxv}]')
        return (value-self.minv)/(self.maxv-self.minv)

    def value(self, scale: float) -> float:
        """convert to value from scaled value

        :param scale: scaled value
        :type scale: float
        """
        if scale < 0 or scale > 1.0:
            raise ValueError(
                f'{scale} outside interval [0,1]')
        return self.minv+scale*(self.maxv-self.minv)

    def scale2int(self, scale: float) -> int:
        """convert scale to integer

        :param scale: scaled value
        :type scale: float
        """
        if scale < 0 or scale > 1.0:
            raise ValueError(
                f'{scale} outside interval [0,1]')
        return round(scale/self.resolution)

    def int2scale(self, iscale: int) -> float:
        """convert integer scale to float

        :param iscale: scaled value
        :type iscale: int
        """
        return iscale*self.resolution

    def value2int(self, value: float) -> int:
        """scale value and convert to integer

        :param value: value to be scaled and converted
        :type value: float
        """
        return self.scale2int(self.scale(value))

    def int2value(self, iscale: int) -> float:
        """convert integer scale to value

        :param iscale: scaled value
        :type iscale: int
        """
        return self.value(self.int2scale(iscale))


class ObjectiveFunction:
    """class maintaining a lookup table for an objective function

    :param basedir: the directory in which the lookup table is kept
    :type basedir: Path
    :param parameters: a dictionary mapping parameter names to the range of
        permissible parameter values
    """

    def __init__(self, basedir: Path, parameters: Mapping[str, Parameter]):
        """constructor"""

        if len(parameters) == 0:
            raise RuntimeError('no parameters given')

        self._parameters = parameters
        self._log = logging.getLogger('OptClim2.ObjectiveFunction')

        dbName = basedir/'objective_function.sqlite'

        # generate database query strings
        paramlist = list(parameters.keys())
        paramlist.sort()
        slct = []
        insrt = []
        for p in paramlist:
            # make sure that parameter names are alpha numeric to avoid
            # sql injection attacks
            if not p.isalnum():
                raise ValueError(f'{p} should be alpha-numeric')
            slct.append(f'{p}=:{p}')
            insrt.append(f':{p}')
        insrt.append('"n"')
        insrt.append('null')
        self._select_str = ' and '.join(slct)
        self._insert_str = '('+','.join(insrt)+')'

        if not dbName.exists():
            self._log.info('create db')
            self._con = sqlite3.connect(dbName)

            cur = self.con.cursor()
            cur.execute(
                """create table if not exists parameters
                (name text, minv real, maxv real, resolution real);
                """)
            cols = []
            for p in paramlist:
                cols.append(f'{p} integer')
                cur.execute("insert into parameters values (?,?,?,?);",
                            (p, parameters[p].minv, parameters[p].maxv,
                             parameters[p].resolution))
            cols.append("state text")
            cols.append("result float")
            cur.execute(
                "create table if not exists lookup ({0});".format(
                    ",".join(cols)))
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
                if abs(res-parameters[p].resolution) > min(
                        res, parameters[p].resolution):
                    self._log.error(f'resolution of {p} does not match')
                    error = True
                if abs(minv-parameters[p].minv) > parameters[p].resolution:
                    self._log.error(f'min value of {p} does not match')
                    error = True
                if abs(maxv-parameters[p].maxv) > parameters[p].resolution:
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

    def _getiparam(self, params):
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

    def __call__(self, params):
        iparam = self._getiparam(params)
        cur = self.con.cursor()
        cur.execute(
            'select state, result from lookup where '+self._select_str,
            iparam)
        r = cur.fetchone()
        if r is None:
            cur.execute(
                'insert into lookup values '+self._insert_str,
                iparam)
            self.con.commit()

            raise OptClimNewRun()

        if r[0] == 'c':
            return r[1]
        else:
            return random.random()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    params = {'a': Parameter(1, 2), 'b': Parameter(-1, 1)}
    objFun = ObjectiveFunction(Path('/tmp'), params)

    print(objFun({'a': 1, 'b': 0}))
