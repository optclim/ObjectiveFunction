__all__ = ['ObjectiveFunctionSimObs']

from typing import Mapping, Sequence
from pathlib import Path
import pandas
import numpy

from .parameter import Parameter
from .objective_function import ObjectiveFunction, LookupState
from .model import DBRunPath, DBObsName


class ObjectiveFunctionSimObs(ObjectiveFunction):
    """class maintaining a lookup table for an objective function

    store the name of a file containing the residuals

    :param study: the name of the study
    :type study: str
    :param basedir: the directory in which the lookup table is kept
    :type basedir: Path
    :param parameters: a dictionary mapping parameter names to the range of
        permissible parameter values
    :param observationNames: a list of observation names
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
                 observationNames: Sequence[str],
                 scenario=None, db=None, prelim=True):
        """constructor"""

        super().__init__(study, basedir, parameters,
                         scenario=scenario, db=db, prelim=prelim)

        if self._is_new:
            for name in observationNames:
                DBObsName(name=name, study=self._study)
            try:
                self.session.commit()
            except Exception as e:
                self._log.error(e)
                raise RuntimeError('failed to set observation names')
        else:
            # make sure that observation names match
            error = False
            if len(self._study.obsnames) != len(observationNames):
                self._log.error(
                    f'number of parameters in {study} does not match')
                error = True
            else:
                for obsName in self._study.obsnames:
                    if obsName.name not in observationNames:
                        self._log.error(
                            f'observation name {obsName} missing '
                            'from configuration')
                        error = True
            if error:
                raise RuntimeError('configuration does not match database')

    @property
    def observationNames(self):
        obsNames = []
        for on in self._study.obsnames:
            obsNames.append(on.name)
        return obsNames

    @property
    def num_residuals(self):
        """the number of residuals"""
        return len(self._study.obsnames)

    def _check_simobs(self, simobs):
        simobs = pandas.Series(simobs)
        error = False
        if len(simobs) != self.num_residuals:
            self._log.error("length of observations does not match")
            error = True
        for n in self.observationNames:
            if n not in simobs.index:
                self._log.error(f"observation {n} missing from simobs")
                error = True
        if error:
            raise RuntimeError("observation names do not match")
        return simobs

    def get_simobs(self, params, scenario=None):
        """look up parameters

        :param parms: dictionary containing parameter values
        :param scenario: the name of the scenario
        :raises NewRun: when lookup fails
        :raises Waiting: when completed entries are required
        :return: returns simulated observations if lookup succeeded or None
        :rtype: pandas.Series
        """

        run = self._lookupRun(params, scenario=scenario)
        if run.state != LookupState.COMPLETED:
            return None
        else:
            result = pandas.read_json(run.path, typ='series')
            self._check_simobs(result)
        return result

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
        result = self.get_simobs(params, scenario=scenario)
        if result is None:
            return numpy.random.rand(self.num_residuals)
        else:
            return result.values

    def set_result(self, params, result, scenario=None, force=False):
        """set the result for a paricular parameter set

        :param parms: dictionary of parameters
        :param result: residuals to store
        :param scenario: the name of the scenario
        :param force: force setting results irrespective of state
        :type result: numpy.ndarray
        """
        result = self._check_simobs(result)

        run = self._getRun(params, scenario=scenario)
        if (run.state.value > LookupState.CONFIGURED.value
            and run.state != LookupState.COMPLETED) or force:  # noqa W503
            # store residuals in file
            fname = self.basedir / f'simobs_{run.id}.json'
            result.to_json(fname)
            run.path = str(fname)
            run.state = LookupState.COMPLETED
            self.session.commit()
        else:
            raise RuntimeError(f'parameter set is in wrong state {run.state}')
