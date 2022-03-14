import pytest
from ObjectiveFunction import ParameterInt


def test_parameter_bad_type():
    """check type"""
    with pytest.raises(TypeError):
        ParameterInt(2.0, 1, 3)
    with pytest.raises(TypeError):
        ParameterInt(2, 1.0, 3)
    with pytest.raises(TypeError):
        ParameterInt(2, 1, 3.0)


def test_parameter_bad_range():
    """check that misordering of min/max value is caught"""
    with pytest.raises(ValueError):
        ParameterInt(1, 3, 1)


def test_parameter_value_outside_range():
    """check that value outside range is caught"""
    with pytest.raises(ValueError):
        ParameterInt(5, 1, 3)


@pytest.fixture
def param():
    return ParameterInt(0, -10, 20)


def test_param_attribs(param):
    """check that we get expected attributes"""
    assert param.value == 0
    assert param.minv == -10
    assert param.maxv == 20
    assert param.constant is False


def test_param_assign_value(param):
    """check value assignment works"""
    v = 5
    param.value = v
    assert param.value == v


def test_param_assing_value_outside_range(param):
    """check value outside range is caught"""
    for v in [-11, 21]:
        with pytest.raises(ValueError):
            param.value = v


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
