import pytest
import numpy

from OptClim2 import ObjectiveFunction
from OptClim2 import ParameterFloat


class DummyObjectiveFunction(ObjectiveFunction):
    def get_result(self, params, scenario=None):
        raise NotImplementedError

    def set_result(self, params, result, scenario=None):
        raise NotImplementedError


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("objective_function")
    return res


@pytest.fixture
def objfunmem(paramsA):
    return DummyObjectiveFunction("study", "", paramsA, db='sqlite://')


def test_study_name(objfunmem):
    assert objfunmem.study == "study"


def test_num_params(objfunmem):
    assert objfunmem.num_params == 3


def test_lower_bounds(objfunmem):
    assert numpy.all(
        objfunmem.lower_bounds == numpy.array((-1, 0, -5)))


def test_upper_bounds(objfunmem):
    assert numpy.all(
        objfunmem.upper_bounds == numpy.array((1, 2, 0)))


def test_values2params_fail(objfunmem):
    with pytest.raises(AssertionError):
        objfunmem.values2params((0, 1))
    with pytest.raises(AssertionError):
        objfunmem.values2params((0, 1, 3, 4))


def test_values2params(objfunmem):
    assert objfunmem.values2params((0, 1, 2)) == {
        'a': 0, 'b': 1, 'c': 2}


def test_empty_scenarios(objfunmem):
    scenarios = objfunmem.scenarios
    assert scenarios == []


def test_select_scenario_nocreate(objfunmem):
    with pytest.raises(LookupError):
        objfunmem._select_scenario('not_here', create=False)


def test_select_scenario(objfunmem):
    name = 'scenario'
    scenario = objfunmem._select_scenario(name)
    assert scenario.name == name
    assert name in objfunmem.scenarios


def test_getScenario_nocreate(objfunmem):
    with pytest.raises(LookupError):
        objfunmem.getScenario('not_here')


def test_getScenario_fail(objfunmem):
    with pytest.raises(RuntimeError):
        objfunmem.getScenario()


def test_getScenario_create(objfunmem):
    name = 'scenario'
    scenario = objfunmem._select_scenario(name)
    assert scenario.name == name
    assert name in objfunmem.scenarios


def test_setDefaultScenario(objfunmem):
    name = 'scenario'
    objfunmem.setDefaultScenario(name)
    assert objfunmem._scenario.name == name
    assert name in objfunmem.scenarios


@pytest.fixture
def objfunmem_scenario(paramsA):
    return DummyObjectiveFunction("study", "", paramsA,
                                  db='sqlite://', scenario='scenario')


def test_objfun_with_scenario(objfunmem_scenario):
    name = 'scenario'
    assert objfunmem_scenario._scenario.name == name
    assert name in objfunmem_scenario.scenarios


def test_objfun_get_default_scenario(objfunmem_scenario):
    name = 'scenario'
    scenario = objfunmem_scenario.getScenario()
    assert scenario.name == name
    assert name in objfunmem_scenario.scenarios


def test_get_new_none(objfunmem_scenario):
    with pytest.raises(RuntimeError):
        objfunmem_scenario.get_new()


class TestObjectiveFunction:
    @pytest.fixture
    def objfun(self):
        return DummyObjectiveFunction

    @pytest.fixture
    def objectiveA(self, objfun, rundir, paramsA):
        return objfun("study", rundir, paramsA, scenario="scenario")

    def test_objective_function_read(self, objfun, objectiveA, paramsA):
        o = objectiveA
        objfun("study", o.basedir, paramsA)

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
            objfun("study", o.basedir, paramsB)

    def test_objective_function_read_fail_config(
            self, objfun, objectiveA, paramsB):
        o = objectiveA
        # wrong number of parameters in config
        with pytest.raises(RuntimeError):
            objfun("study", o.basedir, paramsB)

    def test_objective_function_read_fail_db(
            self, objfun, objectiveA, paramsA):
        o = objectiveA
        paramsA['d'] = ParameterFloat(10, 20)
        # wrong number of parameters in db
        with pytest.raises(RuntimeError):
            objfun("study", o.basedir, paramsA)
