__all__ = ['ObjectiveFunction']

import logging
from typing import Mapping
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import numpy
import pandas
from abc import ABCMeta, abstractmethod

from .parameter import Parameter
from .model import Base, DBStudy, getDBParameter, DBScenario, DBRun
from .common import PreliminaryRun, NewRun, Waiting
from .common import LookupState


class SessionMaker:
    _sessions = {}

    def __call__(self, connstr):
        if connstr not in self._sessions:
            engine = create_engine(connstr)
            Base.metadata.create_all(engine)
            self._sessions[connstr] = sessionmaker(bind=engine)
        return self._sessions[connstr]()


_sessionmaker = SessionMaker()


class ObjectiveFunction(metaclass=ABCMeta):
    """class maintaining a lookup table for an objective function

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

    _Run = DBRun

    def __init__(self, study: str, basedir: Path,  # noqa C901
                 parameters: Mapping[str, Parameter],
                 scenario=None, db=None, prelim=True):
        """constructor"""

        if len(parameters) == 0:
            raise RuntimeError('no parameters given')

        self._parameters = parameters
        self._constant_parameters = {}
        self._active_parameters = {}
        for p in self.parameters:
            if self.parameters[p].constant:
                self._constant_parameters[p] = self.parameters[p]
            else:
                self._active_parameters[p] = self.parameters[p]
        self._paramlist = tuple(
            sorted(list(self.parameters.keys())))
        self._active_paramlist = tuple(
            sorted(list(self.active_parameters.keys())))
        self._log = logging.getLogger(
            f'ObjectiveFunction.{self.__class__.__name__}')
        self._basedir = basedir
        self._session = None
        self._prelim = prelim

        if db is None:
            dbName = 'sqlite:///' + str(basedir / 'objective_function.sqlite')
        else:
            dbName = db

        self._session = _sessionmaker(dbName)

        # get the study
        self._study = self._session.query(DBStudy).filter_by(
            name=study).one_or_none()
        if self._study is None:
            self._log.debug(f'creating study {study}')
            self._study = DBStudy(name=study)
            self.session.add(self._study)
            for p in self.parameters:
                getDBParameter(self._study, p, self.parameters[p])
            self.session.commit()
            self._is_new = True
        else:
            self._log.debug(f'loading study {study}')
            error = False
            if self.num_params != len(self._study.parameters):
                self._log.error(
                    f'number of parameters in {study} does not match')
                error = True
            else:
                for p in self._study.parameters:
                    if p.name not in self.parameters:
                        self._log.error(
                            f'parameter {p.name} missing from configuration')
                        error = True
                        continue
                    if self.parameters[p.name] != p.param:
                        self._log.error(f'parameter {p.name} does not match')
                        self._log.error(f'parameter in DB: {p.param}')
                        self._log.error(
                            f'parameter in config: {self.parameters[p.name]}')
                        error = True
            if error:
                raise RuntimeError('configuration does not match database')
            self._is_new = False

        self._lb = None
        self._ub = None

        self._scenario = None
        if scenario is not None:
            self.setDefaultScenario(scenario)

    @property
    def basedir(self):
        """the basedirectory"""
        return self._basedir

    @property
    def session(self):
        return self._session

    @property
    def prelim(self):
        return self._prelim

    @property
    def study(self):
        """the name of the study"""
        return str(self._study.name)

    @property
    def num_params(self):
        """the number of parameters"""
        return len(self._parameters)

    @property
    def num_active_params(self):
        """the number of parameters"""
        return len(self._active_parameters)

    @property
    def parameters(self):
        """dictionary of parameters"""
        return self._parameters

    @property
    def active_parameters(self):
        """the constant parameters"""
        return self._active_parameters

    @property
    def constant_parameters(self):
        """the constant parameters"""
        return self._constant_parameters

    def getLowerBounds(self):
        """an array containing the lower bounds"""
        if self._lb is None:
            self._lb = []
            for p in self._active_paramlist:
                self._lb.append(self.parameters[p].minv)
            self._lb = numpy.array(self._lb)
        return self._lb

    def getUpperBounds(self):
        """an array containing the upper bounds"""
        if self._ub is None:
            self._ub = []
            for p in self._active_paramlist:
                self._ub.append(self.parameters[p].maxv)
            self._ub = numpy.array(self._ub)
        return self._ub

    @property
    def lower_bounds(self):
        """an array containing the lower bounds"""
        return self.getLowerBounds()

    @property
    def upper_bounds(self):
        """an array containing the upper bounds"""
        return self.getUpperBounds()

    def values2params(self, values):
        """create a dictionary of parameter values from list of values
        :param values: a list/tuple of values
        :return: a dictionary of parameters
        """
        params = {}
        if len(values) == len(self.parameters):
            for i, p in enumerate(self._paramlist):
                params[p] = values[i]
        elif len(values) == len(self.active_parameters):
            for i, p in enumerate(self._active_paramlist):
                params[p] = values[i]
            for p in self.constant_parameters:
                params[p] = self.constant_parameters[p].value
        else:
            raise RuntimeError('Wrong number of parameters')

        return params

    def params2values(self, params, include_constant=True):
        """create an array of values from a dictionary of parameters
        :param params: a dictionary of parameters
        :param include_constant: set to False to exclude constant parameters
        :return: a array of values
        """
        values = []
        for p in self._paramlist:
            if self.parameters[p].constant:
                if include_constant:
                    values.append(self.parameters[p].value)
            else:
                values.append(params[p])
        return numpy.array(values)

    @property
    def scenarios(self):
        """the list of scenario names associated with study"""
        scenarios = [s.name for s in self._study.scenarios]
        return scenarios

    def _select_scenario(self, name, create=True):
        """select a scenario

        :param name: name of scenario
        :type name: str
        :param create: create scenario if it does not already exist
        :type create: bool
        """

        scenario = self._session.query(DBScenario).filter_by(
            name=name, study=self._study).one_or_none()
        if scenario is None:
            if create:
                self._log.debug(f'create scenario {name}')
                scenario = DBScenario(name=name, study=self._study)
                self.session.commit()
            else:
                raise LookupError(
                    f'study {self.study} has no scenario {name}')
        return scenario

    def setDefaultScenario(self, name):
        """set the default scenario

        :param name: name of scenario
        :type name: str
        """
        self._scenario = self._select_scenario(name)

    def getScenario(self, scenario=None):
        """get scenario object

        :param scenario: the name of the scenario or None
                           if None get the default scenario
        :type scenario: str
        """
        if scenario is not None:
            s = self._select_scenario(scenario, create=False)
        else:
            s = self._scenario
        if s is None:
            raise RuntimeError('no scenario selected')
        return s

    def _getRun(self, parameters, scenario=None):
        """look up parameters

        :param parms: dictionary containing parameter values
        :param scenario: the name of the scenario
        :raises LookupError: when lookup fails
        """
        s = self.getScenario(scenario)

        dbParams = {}
        dbParams['runid'] = []
        for p in s.study.parameters:
            dbParams[p.name] = []
        for run in s.runs:
            dbParams['runid'].append(run.id)
            for p in run.values:
                dbParams[p.parameter.name].append(p.value)

        # turn into pandas dataframe to query
        dbParams = pandas.DataFrame(dbParams)
        # construct query
        query = []
        for p in self.parameters:
            if self.parameters[p].constant:
                v = self.parameters[p].value
            else:
                v = parameters[p]
            query.append('({}=={})'.format(
                p, self.parameters[p].transform(v)))
        query = ' & '.join(query)
        runid = dbParams.query(query)

        if len(runid) == 0:
            raise LookupError("no entry for parameter set found")
        runid = int(runid.runid.iloc[0])
        run = self.session.query(self._Run).filter_by(id=runid).one()
        return run

    def getRunID(self, parameters, scenario=None):
        """get ID of run

        :param parms: dictionary containing parameter values
        :param scenario: the name of the scenario
        """
        run = self._getRun(parameters, scenario=scenario)
        return run.id

    def state(self, parameters, scenario=None):
        """get run state

        :param parms: dictionary containing parameter values
        :param scenario: the name of the scenario
        """
        run = self._getRun(parameters, scenario=scenario)
        return run.state

    def _lookupRun(self, parameters, scenario=None):
        """look up parameters

        :param parmeters: dictionary containing parameter values
        :param scenario: the name of the scenario
        :raises NewRun: when lookup fails
        :raises Waiting: when completed entries are required
        """
        s = self.getScenario(scenario)

        run = None
        try:
            run = self._getRun(parameters, scenario=scenario)
        except LookupError:
            pass

        if run is None:
            # check if we already have a provisional entry
            run = self.session.query(self._Run).filter_by(
                scenario=s, state=LookupState.PROVISIONAL).one_or_none()
            if run is not None:
                # we already have a provisional value
                # delete the previous one and wait
                self._log.info('remove provisional parameter set')
                self.session.delete(run)
                self.session.commit()
                raise Waiting

            # create a new entry
            self._log.info('new provisional parameter set')
            run = self._Run(s, parameters)
            if self.prelim:
                run.state = LookupState.PROVISIONAL
                self.session.commit()
                raise PreliminaryRun
            else:
                run.state = LookupState.NEW
                self.session.commit()
                raise NewRun

        if run.state == LookupState.PROVISIONAL:
            self._log.info('provisional parameter set changed to new')
            run.state = LookupState.NEW
            self.session.commit()
            raise NewRun
        elif run.state == LookupState.COMPLETED:
            self._log.debug('hit completed parameter set')
        else:
            self._log.debug('hit new/active parameter set')

        return run

    def get_new(self, scenario=None):
        """get a set of parameters that are not yet processed

        :param scenario: the name of the scenario

        The parameter set changes set from new to active

        :return: dictionary of parameter values for which to compute the model
        :raises RuntimeError: if there is no new parameter set
        """

        s = self.getScenario(scenario)

        run = self.session.query(DBRun)\
                          .filter_by(scenario=s,
                                     state=LookupState.NEW)\
                          .with_for_update().first()

        if run is None:
            raise RuntimeError('no new parameter sets')

        run.state = LookupState.ACTIVE

        self.session.commit()

        return run.parameters

    @abstractmethod
    def get_result(self, params, scenario=None):
        pass

    @abstractmethod
    def set_result(self, params, result, scenario=None, force=False):
        pass

    def __call__(self, x, grad):
        """look up parameters
        :param x: vector containing parameter values
        :param grad: vector of length 0
        :type grad: numpy.ndarray
        :raises NewRun: when lookup fails
        :raises Waiting: when completed entries are required
        :return: returns the value if lookup succeeds and state is completed
                 return a random value otherwise
        :rtype: float
        """
        if grad.size > 0:
            raise RuntimeError(
                'ObjectiveFunction only supports derivative '
                'free optimisations')
        return self.get_result(self.values2params(x))


if __name__ == '__main__':
    from .parameter import ParameterFloat

    logging.basicConfig(level=logging.DEBUG)

    params = {'a': ParameterFloat(-1, 1),
              'b': ParameterFloat(0, 2, 1e-7),
              'c': ParameterFloat(-5, 0)}

    class DummyObjectiveFunction(ObjectiveFunction):
        def get_result(self, params, scenario=None):
            raise NotImplementedError

    def set_result(self, params, result, scenario=None):
        raise NotImplementedError

    objfun = DummyObjectiveFunction("test_study", Path('/tmp'),
                                    params, scenario="test_scenario")

    pset1 = {'a': 0, 'b': 1, 'c': -2}
    pset2 = {'a': 0.5, 'b': 1, 'c': -2}
    pset3 = {'a': 0.5, 'b': 1.5, 'c': -2}
    # print(objfun.getRunID(pset3))
    print(objfun.state(pset1))
    # objfun._lookupRun(pset1)

    print(objfun.get_new())
