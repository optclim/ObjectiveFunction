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
    assert objectiveA._insert_str == '(null,:a,:b,:c,"n",null)'


def test_select_new_str(objectiveA):
    assert objectiveA._select_new_str == 'a, b, c'


def test_values2params(objectiveA):
    assert objectiveA._values2params((0, 1, 2)) == {
        'a': 0, 'b': 1, 'c': 2}


def test_values2params_fail(objectiveA):
    with pytest.raises(AssertionError):
        objectiveA._values2params((0, 1))
    with pytest.raises(AssertionError):
        objectiveA._values2params((0, 1, 3, 4))


@pytest.fixture
def valuesA():
    return {'a': 0., 'b': 1., 'c': -2}


@pytest.fixture
def resultA():
    return 1000.


def test_missing_param_set(objectiveA, valuesA):
    # these should all fail because the param set is missing
    with pytest.raises(LookupError):
        objectiveA.state(valuesA)
    with pytest.raises(LookupError):
        objectiveA.set_result(valuesA, resultA)


def test_get_new_fail(objectiveA, valuesA):
    # no entries yet
    with pytest.raises(RuntimeError):
        objectiveA.get_new()


def test_lookup_parameters(objectiveA, valuesA, resultA):
    # should fail since the values are not in the lookup table
    with pytest.raises(OptClimNewRun):
        objectiveA(valuesA)
    # the state should be new now
    assert objectiveA.state(valuesA) == 'n'
    # should succeed but return a random value
    r = objectiveA(valuesA)
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
    assert objectiveA.state(valuesA) == 'a'
    # should fail now because if already consumed it
    with pytest.raises(RuntimeError):
        objectiveA.get_new()


def test_set_result(objectiveA, valuesA, resultA):
    # set the value
    objectiveA.set_result(valuesA, resultA)
    # state should be completed
    assert objectiveA.state(valuesA) == 'c'
    # and we should be able to retrieve the value
    assert objectiveA(valuesA) == resultA
    # this should fail because the value is in the wrong
    # state
    with pytest.raises(RuntimeError):
        objectiveA.set_result(valuesA, resultA)
