import pytest
import numpy

from ObjectiveFunction import ObjectiveFunctionMisfit
from test_ObjectiveFunction import TestObjectiveFunction as TOF
from ObjectiveFunction import LookupState
from ObjectiveFunction import PreliminaryRun, NewRun, NoNewRun


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("of-misfit")
    return res


@pytest.fixture
def resultA():
    return 1000.


class TestObjectiveFunctionMisfit(TOF):
    @pytest.fixture
    def objfun(self):
        return ObjectiveFunctionMisfit

    @pytest.fixture
    def objectiveAvA(self, objectiveA, valuesA):
        o = objectiveA
        try:
            o.get_result(valuesA)
        except PreliminaryRun:
            pass
        try:
            o.get_result(valuesA)
        except NewRun:
            pass
        return o

    def test_empty_lookup(self, objectiveA, valuesA, resultA):
        # these should all fail because the param set is missing
        with pytest.raises(LookupError):
            objectiveA.state(valuesA)
        with pytest.raises(LookupError):
            objectiveA.set_result(valuesA, resultA)
        with pytest.raises(LookupError):
            objectiveA.get_with_state(LookupState.NEW)
        with pytest.raises(NoNewRun):
            objectiveA.get_new()

    def test_lookup_parameters_two(self, objectiveA, valuesA, resultA):
        # test what happens when we insert a new value

        # first time we lookup a parameter should raise PreliminaryRun
        with pytest.raises(PreliminaryRun):
            objectiveA.get_result(valuesA)
        # the state should be provisional now
        assert objectiveA.state(valuesA) == LookupState.PROVISIONAL
        # a second lookup of the same parameter should get a new exception
        with pytest.raises(NewRun):
            objectiveA.get_result(valuesA)
        # the state should be new now
        assert objectiveA.state(valuesA) == LookupState.NEW
        # should succeed but return a random value
        r = objectiveA.get_result(valuesA)
        assert isinstance(r, float)
        assert r != resultA
        # attempting to set result should fail because
        # parameter set is in wrong state ('n')
        with pytest.raises(RuntimeError):
            objectiveA.set_result(valuesA, resultA)

    def test_setState(self, objectiveAvA, valuesA):
        rid, p = objectiveAvA.get_with_state(LookupState.NEW, with_id=True,
                                             new_state=LookupState.CONFIGURING)
        # the state should be configuring now
        assert objectiveAvA.state(valuesA) == LookupState.CONFIGURING
        objectiveAvA.setState(rid, LookupState.CONFIGURED)
        assert objectiveAvA.state(valuesA) == LookupState.CONFIGURED

    def test_get_with_state(self, objectiveAvA, valuesA):
        p = objectiveAvA.get_with_state(LookupState.NEW,
                                        new_state=LookupState.CONFIGURING)
        assert p == valuesA
        # the state should be configuring now
        assert objectiveAvA.state(valuesA) == LookupState.CONFIGURING
        # should fail now because if already consumed it
        with pytest.raises(LookupError):
            objectiveAvA.get_with_state(LookupState.NEW)

    def test_get_new(self, objectiveAvA, valuesA):
        p = objectiveAvA.get_new()
        assert p == valuesA
        # the state should be new now
        assert objectiveAvA.state(valuesA) == LookupState.ACTIVE
        # should fail now because if already consumed it
        with pytest.raises(NoNewRun):
            objectiveAvA.get_new()

    def test_get_with_state_with_id(self, objectiveAvA, valuesA):
        rid, p = objectiveAvA.get_with_state(LookupState.NEW, with_id=True,
                                             new_state=LookupState.CONFIGURING)
        assert rid == 1
        assert p == valuesA
        # the state should be configuring now
        assert objectiveAvA.state(valuesA) == LookupState.CONFIGURING
        # should fail now because if already consumed it
        with pytest.raises(LookupError):
            objectiveAvA.get_with_state(LookupState.NEW)

    def test_get_new_with_id(self, objectiveAvA, valuesA):
        rid, p = objectiveAvA.get_new(with_id=True)
        assert rid == 1
        assert p == valuesA
        # the state should be new now
        assert objectiveAvA.state(valuesA) == LookupState.ACTIVE
        # should fail now because if already consumed it
        with pytest.raises(NoNewRun):
            objectiveAvA.get_new()

    def test_set_result_force(self, objectiveAvA, valuesA, resultA):
        objectiveAvA.set_result(valuesA, resultA, force=True)
        # state should be completed
        assert objectiveAvA.state(valuesA) == LookupState.COMPLETED
        # and we should be able to retrieve the value
        assert objectiveAvA.get_result(valuesA) == resultA

    def test_set_result(self, objectiveAvA, valuesA, resultA):
        objectiveAvA.get_new()
        # set the value
        objectiveAvA.set_result(valuesA, resultA)
        # state should be completed
        assert objectiveAvA.state(valuesA) == LookupState.COMPLETED
        # and we should be able to retrieve the value
        assert objectiveAvA.get_result(valuesA) == resultA
        # this should fail because the value is in the wrong
        # state
        with pytest.raises(RuntimeError):
            objectiveAvA.set_result(valuesA, resultA)

    def test_call(self, objectiveAvA, valuesA, resultA):
        objectiveAvA.get_new()
        objectiveAvA.set_result(valuesA, resultA)
        assert objectiveAvA(list(valuesA.values()), numpy.array([])) == resultA


class TestObjectiveFunctionMisfitPrelim(TestObjectiveFunctionMisfit):
    @pytest.fixture
    def objectiveA(self, objfun, rundir, paramsA):
        return objfun("study", rundir, paramsA,
                      scenario="scenario", prelim=False)

    @pytest.fixture
    def objectiveAvA(self, objectiveA, valuesA):
        o = objectiveA
        try:
            o.get_result(valuesA)
        except NewRun:
            pass
        return o

    def test_lookup_parameters_two(self, objectiveA, valuesA, resultA):
        # test what happens when we insert a new value

        # a first lookup of the parameter should get a new exception
        with pytest.raises(NewRun):
            objectiveA.get_result(valuesA)
        # the state should be new now
        assert objectiveA.state(valuesA) == LookupState.NEW
        # should succeed but return a random value
        r = objectiveA.get_result(valuesA)
        assert isinstance(r, float)
        assert r != resultA
        # attempting to set result should fail because
        # parameter set is in wrong state ('n')
        with pytest.raises(RuntimeError):
            objectiveA.set_result(valuesA, resultA)
