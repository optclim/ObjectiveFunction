import pytest
import numpy

from OptClim2 import Parameter, ObjectiveFunctionMisfit
from OptClim2 import OptClimPreliminaryRun, OptClimNewRun, OptClimWaiting
from OptClim2 import LookupState


@pytest.fixture
def paramsA():
    return {'a': Parameter(-1, 1),
            'b': Parameter(0, 2, 1e-7),
            'c': Parameter(-5, 0)}


@pytest.fixture
def paramsB():
    return {'a': Parameter(-1, 1),
            'b': Parameter(0, 2, 1e-7)}


@pytest.fixture(scope="session")
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("run1")
    return res


def test_objective_function_create(rundir, paramsA):
    # create a new objective function
    ObjectiveFunctionMisfit(rundir, paramsA)


def test_objective_function_read(rundir, paramsA):
    # read existing function
    ObjectiveFunctionMisfit(rundir, paramsA)


testdata = [
    (-6, 0, 1e-6),
    (-5, 1, 1e-6),
    (-5, 0, 1e-7)]


@pytest.mark.parametrize("minv,maxv,resolution", testdata)
def test_objective_function_read_fail_wrong_values(rundir, paramsB, minv,
                                                   maxv, resolution):
    paramsB['c'] = Parameter(minv, maxv, resolution=resolution)
    with pytest.raises(RuntimeError):
        ObjectiveFunctionMisfit(rundir, paramsB)


def test_objective_function_read_fail_config(rundir, paramsB):
    # wrong number of parameters in config
    with pytest.raises(RuntimeError):
        ObjectiveFunctionMisfit(rundir, paramsB)


def test_objective_function_read_fail_db(rundir, paramsA):
    paramsA['d'] = Parameter(10, 20)
    # wrong number of parameters in db
    with pytest.raises(RuntimeError):
        ObjectiveFunctionMisfit(rundir, paramsA)


@pytest.fixture
def objectiveA(rundir, paramsA):
    return ObjectiveFunctionMisfit(rundir, paramsA)


def test_num_params(objectiveA):
    assert objectiveA.num_params == 3


def test_lower_bounds(objectiveA):
    assert objectiveA.lower_bounds == (-1, 0, -5)


def test_upper_bounds(objectiveA):
    assert objectiveA.upper_bounds == (1, 2, 0)


def test_select_str(objectiveA):
    assert objectiveA._select_str == 'a=:a and b=:b and c=:c'


def test_insert_str(objectiveA):
    assert objectiveA._insert_str == '(null,:a,:b,:c,{},null)'.format(
        LookupState.PROVISIONAL.value)


def test_select_new_str(objectiveA):
    assert objectiveA._select_new_str == 'a, b, c'


def test_values2params(objectiveA):
    assert objectiveA.values2params((0, 1, 2)) == {
        'a': 0, 'b': 1, 'c': 2}


def test_values2params_fail(objectiveA):
    with pytest.raises(AssertionError):
        objectiveA.values2params((0, 1))
    with pytest.raises(AssertionError):
        objectiveA.values2params((0, 1, 3, 4))


def test_params2values(objectiveA):
    assert objectiveA.params2values(
        {'a': 0, 'b': 1, 'c': 2}) == (0, 1, 2)


def test_params2values_fail(objectiveA):
    with pytest.raises(KeyError):
        objectiveA.values2params(
            {'d': 0, 'b': 1, 'c': 2})


@pytest.fixture
def valuesA():
    return {'a': 0., 'b': 1., 'c': -2}


@pytest.fixture
def valuesB():
    return {'a': 0.5, 'b': 1., 'c': -2}


@pytest.fixture
def resultA():
    return 1000.


def test_empty_loopup(objectiveA, valuesA):
    # these should all fail because the param set is missing
    with pytest.raises(LookupError):
        objectiveA.state(valuesA)
    with pytest.raises(LookupError):
        objectiveA.set_result(valuesA, resultA)
    with pytest.raises(RuntimeError):
        objectiveA.get_new()


def test_lookup_parameters_one(objectiveA, valuesA, valuesB, resultA):
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
    # if we lookup a different parameter set with should get a wait exception
    with pytest.raises(OptClimWaiting):
        objectiveA.get_result(valuesB)
    # and the previous entry should be deleted
    with pytest.raises(LookupError):
        objectiveA.state(valuesA)


def test_lookup_parameters_two(objectiveA, valuesA, resultA):
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


def test_get_new(objectiveA, valuesA):
    p = objectiveA.get_new()
    assert p == valuesA
    # the state should be new now
    assert objectiveA.state(valuesA) == LookupState.ACTIVE
    # should fail now because if already consumed it
    with pytest.raises(RuntimeError):
        objectiveA.get_new()


def test_set_result(objectiveA, valuesA, resultA):
    # set the value
    objectiveA.set_result(valuesA, resultA)
    # state should be completed
    assert objectiveA.state(valuesA) == LookupState.COMPLETED
    # and we should be able to retrieve the value
    assert objectiveA.get_result(valuesA) == resultA
    # this should fail because the value is in the wrong
    # state
    with pytest.raises(RuntimeError):
        objectiveA.set_result(valuesA, resultA)


def test_call(objectiveA, valuesA, resultA):
    assert objectiveA(list(valuesA.values()), numpy.array([])) == resultA
