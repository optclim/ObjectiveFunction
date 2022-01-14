import pytest

from OptClim2 import ParameterFloat, ParameterInt


@pytest.fixture
def paramsA():
    return {'a': ParameterFloat(-1, 1),
            'b': ParameterFloat(0, 2, 1e-7),
            'c': ParameterFloat(-5, 0)}


@pytest.fixture
def paramsB():
    return {'a': ParameterFloat(-1, 1),
            'b': ParameterFloat(0, 2, 1e-7)}


@pytest.fixture
def valuesA():
    return {'a': 0., 'b': 1., 'c': -2}


@pytest.fixture
def valuesB():
    return {'a': 0.5, 'b': 1., 'c': -2}


@pytest.fixture
def paramSet():
    return {'af': ParameterFloat(0, 2, 1e-7),
            'bf': ParameterFloat(1, 2, 1e-7),
            'cf': ParameterFloat(0, 3, 1e-7),
            'df': ParameterFloat(0, 2, 1e-6),
            'ai': ParameterInt(0, 2),
            'bi': ParameterInt(1, 2),
            'ci': ParameterInt(0, 3)}
