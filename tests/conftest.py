import pytest

from OptClim2 import Parameter


@pytest.fixture
def paramsA():
    return {'a': Parameter(-1, 1),
            'b': Parameter(0, 2, 1e-7),
            'c': Parameter(-5, 0)}


@pytest.fixture
def paramsB():
    return {'a': Parameter(-1, 1),
            'b': Parameter(0, 2, 1e-7)}


@pytest.fixture
def valuesA():
    return {'a': 0., 'b': 1., 'c': -2}


@pytest.fixture
def valuesB():
    return {'a': 0.5, 'b': 1., 'c': -2}
