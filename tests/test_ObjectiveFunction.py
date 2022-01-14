import pytest

from OptClim2.objective_function_new import ObjectiveFunction
from OptClim2 import ParameterFloat


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("objective_function")
    return res


class TestObjectiveFunction:
    @pytest.fixture
    def objfun(self):
        return ObjectiveFunction

    @pytest.fixture
    def objectiveA(self, objfun, rundir, paramsA):
        return objfun("study", rundir, paramsA)
    
    def test_objective_function_create(self, objfun, rundir, paramsA):
        objfun("study", rundir, paramsA)

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

    def test_num_params(self, objectiveA):
        assert objectiveA.num_params == 3
