import pytest
import numpy

from OptClim2 import ObjectiveFunctionResidual
from test_ObjectiveFunctionMisfit import TestObjectiveFunctionMisfit as TOFM
from OptClim2 import LookupState
from OptClim2 import OptClimPreliminaryRun, OptClimNewRun


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("of-residual")
    return res


@pytest.fixture
def resultA():
    return numpy.arange(20, dtype=float)


class TestObjectiveFunctionResidual(TOFM):
    @pytest.fixture
    def objfun(self):
        return ObjectiveFunctionResidual

    def test_lookup_parameters_two(self, objectiveA, valuesA, resultA):
        # test what happens when we insert a new value

        # first time we lookup a parameter should raise OptClimPreliminaryRun
        with pytest.raises(OptClimPreliminaryRun):
            objectiveA.get_result(valuesA)
        # the state should be provisional now
        assert objectiveA.state(valuesA) == LookupState.PROVISIONAL
        # a second lookup of the same parameter should get a new exception
        with pytest.raises(OptClimNewRun):
            objectiveA.get_result(valuesA)
        # the state should be new now
        assert objectiveA.state(valuesA) == LookupState.NEW
        # should succeed but return a random value
        r = objectiveA.get_result(valuesA)
        assert isinstance(r, numpy.ndarray)
        if r.size == resultA.size:
            assert numpy.all(r != resultA)
        # attempting to set result should fail because
        # parameter set is in wrong state ('n')
        with pytest.raises(RuntimeError):
            objectiveA.set_result(valuesA, resultA)

    def test_set_result(self, objectiveAvA, valuesA, resultA):
        objectiveAvA.get_new()
        # set the value
        objectiveAvA.set_result(valuesA, resultA)
        # state should be completed
        assert objectiveAvA.state(valuesA) == LookupState.COMPLETED
        # and we should be able to retrieve the value
        assert numpy.all(objectiveAvA.get_result(valuesA) == resultA)
        # this should fail because the value is in the wrong
        # state
        with pytest.raises(RuntimeError):
            objectiveAvA.set_result(valuesA, resultA)

    def test_call(self, objectiveAvA, valuesA, resultA):
        objectiveAvA.get_new()
        objectiveAvA.set_result(valuesA, resultA)
        assert numpy.all(
            objectiveAvA(list(valuesA.values()), numpy.array([])) == resultA)
