import pytest
import numpy

from OptClim2 import ObjectiveFunctionMisfit
from OptClim2 import ParameterFloat
from OptClim2 import LookupState
from OptClim2 import OptClimPreliminaryRun, OptClimNewRun, OptClimWaiting


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("of-misfit")
    return res


@pytest.fixture
def resultA():
    return 1000.


class TestObjectiveFunctionMisfit:
    @pytest.fixture
    def objfun(self):
        return ObjectiveFunctionMisfit

    @pytest.fixture
    def objectiveA(self, objfun, rundir, paramsA):
        return objfun(rundir, paramsA)

    @pytest.fixture
    def objectiveAvA(self, objectiveA, valuesA):
        o = objectiveA
        try:
            o.get_result(valuesA)
        except OptClimPreliminaryRun:
            pass
        try:
            o.get_result(valuesA)
        except OptClimNewRun:
            pass
        return o

    def test_objective_function_create(self, objfun, rundir, paramsA):
        objfun(rundir, paramsA)

    def test_objective_function_read(self, objfun, objectiveA, paramsA):
        o = objectiveA
        objfun(o.basedir, paramsA)

    @pytest.mark.parametrize("minv,maxv,resolution",
                             [
                                 (-6, 0, 1e-6),
                                 (-5, 1, 1e-6),
                                 (-5, 0, 1e-7)])
    def test_objective_function_read_fail_wrong_values(
            self, objfun, objectiveA, paramsB, minv, maxv, resolution):
        paramsB['c'] = ParameterFloat(minv, maxv, resolution=resolution)
        o = objectiveA
        with pytest.raises(RuntimeError):
            objfun(o.basedir, paramsB)

    def test_objective_function_read_fail_config(
            self, objfun, objectiveA, paramsB):
        o = objectiveA
        # wrong number of parameters in config
        with pytest.raises(RuntimeError):
            objfun(o.basedir, paramsB)

    def test_objective_function_read_fail_db(
            self, objfun, objectiveA, paramsA):
        o = objectiveA
        paramsA['d'] = ParameterFloat(10, 20)
        # wrong number of parameters in db
        with pytest.raises(RuntimeError):
            objfun(o.basedir, paramsA)

    def test_num_params(self, objectiveA):
        assert objectiveA.num_params == 3

    def test_lower_bounds(self, objectiveA):
        assert numpy.all(
            objectiveA.lower_bounds == numpy.array((-1, 0, -5)))

    def test_upper_bounds(self, objectiveA):
        assert numpy.all(
            objectiveA.upper_bounds == numpy.array((1, 2, 0)))

    def test_select_str(self, objectiveA):
        assert objectiveA._select_str == 'a=:a and b=:b and c=:c'

    def test_insert_str(self, objectiveA):
        assert objectiveA._insert_str == '(null,:a,:b,:c,{},null)'.format(
            LookupState.PROVISIONAL.value)

    def test_select_new_str(self, objectiveA):
        assert objectiveA._select_new_str == 'a, b, c'

    def test_values2params(self, objectiveA):
        assert objectiveA.values2params((0, 1, 2)) == {
            'a': 0, 'b': 1, 'c': 2}

    def test_values2params_fail(self, objectiveA):
        with pytest.raises(AssertionError):
            objectiveA.values2params((0, 1))
        with pytest.raises(AssertionError):
            objectiveA.values2params((0, 1, 3, 4))

    def test_params2values(self, objectiveA):
        assert numpy.all(
            objectiveA.params2values(
                {'a': 0, 'b': 1, 'c': 2}) == numpy.array((0, 1, 2)))

    def test_params2values_fail(self, objectiveA):
        with pytest.raises(KeyError):
            objectiveA.values2params(
                {'d': 0, 'b': 1, 'c': 2})

    def test_empty_lookup(self, objectiveA, valuesA):
        # these should all fail because the param set is missing
        with pytest.raises(LookupError):
            objectiveA.state(valuesA)
        with pytest.raises(LookupError):
            objectiveA.set_result(valuesA, resultA)
        with pytest.raises(RuntimeError):
            objectiveA.get_new()

    def test_lookup_parameters_one(
            self, objectiveA, valuesA, valuesB, resultA):
        # test what happens when we insert a new value

        # first time we lookup a parameter should raise OptClimPreliminaryRun
        with pytest.raises(OptClimPreliminaryRun):
            objectiveA.get_result(valuesA)
        # the state should be provisional now
        assert objectiveA.state(valuesA) == LookupState.PROVISIONAL
        # attempting to set result should fail because
        # parameter set is not in the active state
        with pytest.raises(RuntimeError):
            objectiveA.set_result(valuesA, resultA)
        # if we lookup a different parameter set with should get a
        # wait exception
        with pytest.raises(OptClimWaiting):
            objectiveA.get_result(valuesB)
        # and the previous entry should be deleted
        with pytest.raises(LookupError):
            objectiveA.state(valuesA)

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
        assert isinstance(r, float)
        assert r != resultA
        # attempting to set result should fail because
        # parameter set is in wrong state ('n')
        with pytest.raises(RuntimeError):
            objectiveA.set_result(valuesA, resultA)

    def test_get_new(self, objectiveAvA, valuesA):
        p = objectiveAvA.get_new()
        assert p == valuesA
        # the state should be new now
        assert objectiveAvA.state(valuesA) == LookupState.ACTIVE
        # should fail now because if already consumed it
        with pytest.raises(RuntimeError):
            objectiveAvA.get_new()

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
