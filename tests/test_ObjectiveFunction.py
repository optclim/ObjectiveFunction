import pytest
import numpy

from OptClim2 import Parameter
from OptClim2 import LookupState
from OptClim2.objective_function import ObjectiveFunction


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
    res = tmpdir_factory.mktemp("of")
    return res


def test_objective_function_create(rundir, paramsA):
    # create a new objective function
    ObjectiveFunction(rundir, paramsA)


def test_objective_function_read(rundir, paramsA):
    # read existing function
    ObjectiveFunction(rundir, paramsA)


testdata = [
    (-6, 0, 1e-6),
    (-5, 1, 1e-6),
    (-5, 0, 1e-7)]


@pytest.mark.parametrize("minv,maxv,resolution", testdata)
def test_objective_function_read_fail_wrong_values(rundir, paramsB, minv,
                                                   maxv, resolution):
    paramsB['c'] = Parameter(minv, maxv, resolution=resolution)
    with pytest.raises(RuntimeError):
        ObjectiveFunction(rundir, paramsB)


def test_objective_function_read_fail_config(rundir, paramsB):
    # wrong number of parameters in config
    with pytest.raises(RuntimeError):
        ObjectiveFunction(rundir, paramsB)


def test_objective_function_read_fail_db(rundir, paramsA):
    paramsA['d'] = Parameter(10, 20)
    # wrong number of parameters in db
    with pytest.raises(RuntimeError):
        ObjectiveFunction(rundir, paramsA)


@pytest.fixture
def objectiveA(rundir, paramsA):
    return ObjectiveFunction(rundir, paramsA)


def test_num_params(objectiveA):
    assert objectiveA.num_params == 3


def test_lower_bounds(objectiveA):
    assert numpy.all(
        objectiveA.lower_bounds == numpy.array((-1, 0, -5)))


def test_upper_bounds(objectiveA):
    assert numpy.all(
        objectiveA.upper_bounds == numpy.array((1, 2, 0)))


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
    assert numpy.all(
        objectiveA.params2values(
            {'a': 0, 'b': 1, 'c': 2}) == numpy.array((0, 1, 2)))


def test_params2values_fail(objectiveA):
    with pytest.raises(KeyError):
        objectiveA.values2params(
            {'d': 0, 'b': 1, 'c': 2})
