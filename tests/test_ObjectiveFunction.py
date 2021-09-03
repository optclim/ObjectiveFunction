import pytest

from OptClim2.objective_function import Parameter, ObjectiveFunction


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
    (-5, 0, 1e-7)
    ]


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
