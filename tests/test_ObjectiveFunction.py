import pytest

from OptClim2.objective_function_new import ObjectiveFunction
from OptClim2 import ParameterFloat


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("objective_function")
    return res


@pytest.fixture
def objfunmem(paramsA):
    return ObjectiveFunction("study", "", paramsA, db='sqlite://')


def test_study_name(objfunmem):
    assert objfunmem.study == "study"


def test_num_params(objfunmem):
    assert objfunmem.num_params == 3


def test_empty_simulations(objfunmem):
    sims = objfunmem.simulations
    assert sims == []


def test_select_simulation_nocreate(objfunmem):
    with pytest.raises(LookupError):
        objfunmem._select_simulation('not_here', create=False)


def test_select_simulation(objfunmem):
    name = 'simulation'
    sim = objfunmem._select_simulation(name)
    assert sim.name == name
    assert name in objfunmem.simulations


def test_getSimulation_nocreate(objfunmem):
    with pytest.raises(LookupError):
        objfunmem.getSimulation('not_here', create=False)


def test_getSimulation_fail(objfunmem):
    with pytest.raises(RuntimeError):
        objfunmem.getSimulation()


def test_getSimulation_create(objfunmem):
    name = 'simulation'
    sim = objfunmem.getSimulation(simulation=name)
    assert sim.name == name
    assert name in objfunmem.simulations


def test_setDefaultSimulation(objfunmem):
    name = 'simulation'
    objfunmem.setDefaultSimulation(name)
    assert objfunmem._simulation.name == name
    assert name in objfunmem.simulations


@pytest.fixture
def objfunmem_sim(paramsA):
    return ObjectiveFunction("study", "", paramsA,
                             db='sqlite://', simulation='sim')


def test_objfun_with_sim(objfunmem_sim):
    name = 'sim'
    assert objfunmem_sim._simulation.name == name
    assert name in objfunmem_sim.simulations


def test_objfun_get_default_sim(objfunmem_sim):
    name = 'sim'
    sim = objfunmem_sim.getSimulation()
    assert sim.name == name
    assert name in objfunmem_sim.simulations


class TestObjectiveFunction:
    @pytest.fixture
    def objfun(self):
        return ObjectiveFunction

    @pytest.fixture
    def objectiveA(self, objfun, rundir, paramsA):
        return objfun("study", rundir, paramsA, simulation="sim")

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
