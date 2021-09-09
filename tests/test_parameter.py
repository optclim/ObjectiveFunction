import pytest
from OptClim2 import Parameter


def test_parameter_bad_range():
    """check that misordering of min/max value is caught"""
    with pytest.raises(ValueError):
        Parameter(2, 1)


@pytest.fixture
def param():
    return Parameter(-1, 2.5, resolution=1e-5)


def test_param_attribs(param):
    """check that we get expected attributes"""
    assert param.minv == -1
    assert param.maxv == 2.5
    assert param.resolution == 1e-5


def test_scale_wrong_value(param):
    """check that ValueError is raised when wrong value given"""
    with pytest.raises(ValueError):
        param.scale(-1.5)
    with pytest.raises(ValueError):
        param.scale(2.6)


def test_value_wrong_value(param):
    """check the ValueError is raise when wrong scale given"""
    with pytest.raises(ValueError):
        param.value(-0.1)
    with pytest.raises(ValueError):
        param.value(1.1)


def test_scale2int_wrong_value(param):
    """check the ValueError is raise when wrong scale given"""
    with pytest.raises(ValueError):
        param.scale2int(-0.1)
    with pytest.raises(ValueError):
        param.scale2int(1.1)


testdata = [
    (-1., 0., 0),
    (2.5, 1., 100000),
    (0.75, 0.5, 50000),
    (1., 2./3.5, 57143),
    ]


@pytest.mark.parametrize("value,scale,iscale", testdata)
def test_timedistance_v0(param, value, scale, iscale):
    assert param.scale(value) == scale
    assert param.value(scale) == value
    assert param.scale2int(scale) == iscale
    assert abs(param.int2scale(iscale)-scale) < param.resolution
    assert param.value2int(value) == iscale
    assert abs(param.int2value(iscale)-value) < param.resolution
