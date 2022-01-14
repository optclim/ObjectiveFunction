import pytest
from OptClim2 import ParameterInt


def test_parameter_bad_type():
    """check type"""
    with pytest.raises(TypeError):
        ParameterInt(1.0, 2)
    with pytest.raises(TypeError):
        ParameterInt(1, 2.0)


def test_parameter_bad_range():
    """check that misordering of min/max value is caught"""
    with pytest.raises(ValueError):
        ParameterInt(2, 1)


@pytest.fixture
def param():
    return ParameterInt(-10, 20)


def test_param_attribs(param):
    """check that we get expected attributes"""
    assert param.minv == -10
    assert param.maxv == 20
    assert param.constant is False


def test_scale_wrong_value(param):
    """check that ValueError is raised when wrong value given"""
    with pytest.raises(ValueError):
        param(-11)
    with pytest.raises(ValueError):
        param(21)


@pytest.mark.parametrize("value", range(-5, 5))
def test_param_transform(param, value):
    assert param.transform(value) == value
    assert param.inv_transform(value) == value


def test_eq(paramSet):
    for p in paramSet:
        assert (paramSet['ai'] == paramSet[p]) is ('ai' == p)
