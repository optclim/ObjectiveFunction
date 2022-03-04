import pytest
import pandas
import numpy

from OptClim2 import ObjectiveFunctionSimObs
from OptClim2 import LookupState
from OptClim2 import OptClimNewRun

from test_ObjectiveFunctionResidual import TestObjectiveFunctionResidual as \
    TOFR


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("of-simobs")
    return res


@pytest.fixture
def obsnames():
    return ['simA', 'simC', 'simB']


@pytest.fixture
def resultA(obsnames):
    return pandas.Series(
        numpy.arange(len(obsnames), dtype=float) * 0.5,
        obsnames)


def test_obsname_not_unique(paramsA):
    with pytest.raises(RuntimeError):
        ObjectiveFunctionSimObs("study", "", paramsA, ['A', 'B', 'B'],
                                db='sqlite://')


class TestObjectiveFunctionSimObs(TOFR):
    @pytest.fixture
    def objfun(self, obsnames):
        def wrapper(*args, **kwds):
            return ObjectiveFunctionSimObs(*args, obsnames, **kwds)
        return wrapper

    def test_objective_function_read_fail_obsnames(self, objectiveA, paramsA):
        o = objectiveA
        with pytest.raises(RuntimeError):
            ObjectiveFunctionSimObs("study", o.basedir, paramsA, ['A', 'B'])
        with pytest.raises(RuntimeError):
            ObjectiveFunctionSimObs("study", o.basedir, paramsA,
                                    ['A', 'B', 'wrong'])
        with pytest.raises(RuntimeError):
            ObjectiveFunctionSimObs("study", o.basedir, paramsA,
                                    ['A', 'B', 'C', 'wrong'])

    def test_num_residuals(self, objectiveA, obsnames):
        assert objectiveA.num_residuals == len(obsnames)

    def test_obsnames(self, objectiveA, obsnames):
        assert objectiveA.observationNames == sorted(obsnames)

    def test_check_simobs_wrong_number(self, objectiveA):
        with pytest.raises(RuntimeError):
            objectiveA._check_simobs({'A': 1, 'B': 2})

    def test_check_simobs_wrong_obs(self, objectiveA):
        with pytest.raises(RuntimeError):
            objectiveA._check_simobs({'wrong': 1, 'simB': 2, 'simC': 3})

    def test_lookup_parameters_two(self, objectiveA, valuesA, resultA):
        super().test_lookup_parameters_two(objectiveA, valuesA, resultA)
        # should succeed but return None
        r = objectiveA.get_simobs(valuesA)
        assert r is None

    def test_set_result(self, objectiveAvA, valuesA, resultA):
        super().test_set_result(objectiveAvA, valuesA, resultA)
        # and we should be able to retrieve the value
        r = objectiveAvA.get_simobs(valuesA)
        assert len(r.compare(resultA)) == 0


class TestObjectiveFunctionSimObsPrelim(TestObjectiveFunctionSimObs):
    @pytest.fixture
    def objectiveA(self, objfun, rundir, paramsA):
        return objfun("study", rundir, paramsA,
                      scenario="scenario", prelim=False)

    @pytest.fixture
    def objectiveAvA(self, objectiveA, valuesA):
        o = objectiveA
        try:
            o.get_result(valuesA)
        except OptClimNewRun:
            pass
        return o

    def test_lookup_parameters_two(self, objectiveA, valuesA, resultA):
        # test what happens when we insert a new value

        # a first lookup of the parameter should get a new exception
        with pytest.raises(OptClimNewRun):
            objectiveA.get_result(valuesA)
        # the state should be new now
        assert objectiveA.state(valuesA) == LookupState.NEW
        # should succeed but return a random value
        r = objectiveA.get_result(valuesA)
        assert isinstance(r, numpy.ndarray)
        if r.size == resultA.size:
            assert numpy.all(r != resultA)
        # should succeed but return None
        r = objectiveA.get_simobs(valuesA)
        assert r is None
        # attempting to set result should fail because
        # parameter set is in wrong state ('n')
        with pytest.raises(RuntimeError):
            objectiveA.set_result(valuesA, resultA)
