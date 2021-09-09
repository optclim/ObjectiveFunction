import pytest

from OptClim2.objective_function import Parameter, ObjectiveFunction
from OptClim2.objective_function import OptClimNewRun


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


def test_select_str(objectiveA):
    assert objectiveA._select_str == 'a=:a and b=:b and c=:c'


def test_insert_str(objectiveA):
    assert objectiveA._insert_str == '(:a,:b,:c,"n",null)'


@pytest.fixture
def valuesA():
    return {'a': 0., 'b': 1., 'c': -2}


@pytest.fixture
def resultA():
    return 1000.


def test_first_call(objectiveA, valuesA):
    # should fail since the values are not in the lookup table
    with pytest.raises(OptClimNewRun):
        objectiveA(valuesA)


def test_second_call(objectiveA, valuesA, resultA):
    # should succeed but return a random value
    r = objectiveA(valuesA)
    assert isinstance(r, float)
    assert r != resultA
