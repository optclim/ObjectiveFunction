__all__ = ['ObjectiveFunction']

import logging
from typing import Mapping
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas
from abc import ABCMeta, abstractmethod

from .parameter import Parameter
from .model import Base, DBStudy, getDBParameter, DBSimulation, DBRun
from .common import OptClimPreliminaryRun, OptClimNewRun, OptClimWaiting
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

    _Run = DBRun

    def __init__(self, study: str, basedir: Path,  # noqa C901
                 parameters: Mapping[str, Parameter],
                 simulation=None, db=None):
        """constructor"""

        if len(parameters) == 0:
            raise RuntimeError('no parameters given')

        self._parameters = parameters
        self._log = logging.getLogger(f'OptClim2.{self.__class__.__name__}')
        self._basedir = basedir
        self._session = None

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

        self._simulation = None
        if simulation is not None:
            self.setDefaultSimulation(simulation)

    @property
    def basedir(self):
        """the basedirectory"""
        return self._basedir

    @property
    def session(self):
        return self._session

    @property
    def study(self):
        return str(self._study.name)

    @property
    def num_params(self):
        """the number of parameters"""
        return len(self._parameters)

    @property
    def parameters(self):
        """dictionary of parameters"""
        return self._parameters

    @property
    def simulations(self):
        sims = [s.name for s in self._study.simulations]
        return sims

    def _select_simulation(self, name, create=True):
        """select a simulation

        :param name: name of simulation
        :type name: str
        """

        simulation = self._session.query(DBSimulation).filter_by(
            name=name, study=self._study).one_or_none()
        if simulation is None:
            if create:
                self._log.debug(f'create simulation {name}')
                simulation = DBSimulation(name=name, study=self._study)
                self.session.commit()
            else:
                raise LookupError(
                    f'study {self.study} has no simulation {name}')
        return simulation

    def setDefaultSimulation(self, name):
        """set the default simulation

        :param name: name of simulation
        :type name: str
        """
        self._simulation = self._select_simulation(name)

    def getSimulation(self, simulation=None, create=True):
        if simulation is not None:
            sim = self._select_simulation(simulation, create=create)
        else:
            sim = self._simulation
        if sim is None:
            raise RuntimeError('no simulation selected')
        return sim

    def _getRun(self, parameters, simulation=None):
        sim = self.getSimulation(simulation, create=False)

        dbParams = {}
        dbParams['runid'] = []
        for p in sim.study.parameters:
            dbParams[p.name] = []
        for run in sim.runs:
            dbParams['runid'].append(run.id)
            for p in run.values:
                dbParams[p.parameter.name].append(p.value)

        # turn into pandas dataframe to query
        dbParams = pandas.DataFrame(dbParams)
        # construct query
        query = []
        for p in self.parameters:
            query.append('({}=={})'.format(
                p, self.parameters[p].transform(parameters[p])))
        query = ' & '.join(query)
        runid = dbParams.query(query)

        if len(runid) == 0:
            raise LookupError("no entry for parameter set found")
        runid = int(runid.runid.iloc[0])
        run = self.session.query(self._Run).filter_by(id=runid).one()
        return run

    def getRunID(self, parameters, simulation=None):
        run = self._getRun(parameters, simulation=simulation)
        return run.id

    def state(self, parameters, simulation=None):
        run = self._getRun(parameters, simulation=simulation)
        return run.state

    def _lookupRun(self, parameters, simulation=None):
        sim = self.getSimulation(simulation)

        run = None
        try:
            run = self._getRun(parameters, simulation=simulation)
        except LookupError:
            pass

        if run is None:
            # check if we already have a provisional entry
            run = self.session.query(self._Run).filter_by(
                simulation=sim, state=LookupState.PROVISIONAL).one_or_none()
            if run is not None:
                # we already have a provisional value
                # delete the previous one and wait
                self._log.info('remove provisional parameter set')
                self.session.delete(run)
                self.session.commit()
                raise OptClimWaiting

            # create a new entry
            self._log.info('new provisional parameter set')
            run = self._Run(sim, parameters)
            run.state = LookupState.PROVISIONAL
            self.session.commit()
            raise OptClimPreliminaryRun

        if run.state == LookupState.PROVISIONAL:
            self._log.info('provisional parameter set changed to new')
            run.state = LookupState.NEW
            self.session.commit()
            raise OptClimNewRun
        elif run.state == LookupState.COMPLETED:
            self._log.debug('hit completed parameter set')
        else:
            self._log.debug('hit new/active parameter set')

        return run

    @abstractmethod
    def get_result(self, params, simulation=None):
        pass


if __name__ == '__main__':
    from .parameter import ParameterFloat

    logging.basicConfig(level=logging.DEBUG)

    params = {'a': ParameterFloat(-1, 1),
              'b': ParameterFloat(0, 2, 1e-7),
              'c': ParameterFloat(-5, 0)}

    objfun = ObjectiveFunction("test_study", Path('/tmp'),
                               params, simulation="test_sim")

    pset1 = {'a': 0, 'b': 1, 'c': -2}
    pset2 = {'a': 0.5, 'b': 1, 'c': -2}
    pset3 = {'a': 0.5, 'b': 1.5, 'c': -2}
    print(objfun.getRunID(pset3))
    print(objfun.state(pset1))
    objfun._lookupRun(pset1)
