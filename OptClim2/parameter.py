__all__ = ['Parameter', 'ParameterInt', 'ParameterFloat']

from abc import ABC, abstractmethod
from typing import TypeVar, Generic
import sys

T = TypeVar('T', int, float)


class Parameter(ABC, Generic[T]):
    """a parameter with minimum and maximum value

    :param minv: minimum value (inclusive)
    :param maxv: maximum value (inclusive)
    :param constant: set to True to exclude parameter from optimisation
    :type constant: bool
    """
    def __init__(self, minv: T, maxv: T,
                 constant: bool = False) -> None:
        """constructor"""

        self._minv: T = minv
        self._maxv: T = maxv
        self._constant = bool(constant)
        if self.minv >= self.maxv:
            raise ValueError('minv must be smaller than maxv')

    @property
    def minv(self) -> T:
        """the minimum value the parameter can take"""
        return self._minv

    @property
    def maxv(self) -> T:
        """the maximum value the parameter can take"""
        return self._maxv

    @property
    def constant(self) -> bool:
        """whether the parameter should be excluded from optimisation"""
        return self._constant

    def check_value(self, value: T) -> None:
        if value < self.minv or value > self.maxv:
            raise ValueError(f'value {value} outside bounds '
                             f'[{self.minv}, {self.maxv}]')

    @abstractmethod
    def transform(self, value: T) -> int:
        """transform the value to the internal storage format"""
        pass

    @abstractmethod
    def inv_transform(self, dbval: int) -> T:
        """transform from the internal storage format"""
        pass

    def __call__(self, value: T) -> T:
        """check the value is within the bounds and apply any rounding"""
        return self.inv_transform(self.transform(value))


class ParameterInt(Parameter[int]):
    """a integer parameter with minimum and maximum value

    :param minv: minimum value (inclusive)
    :type minv: int
    :param maxv: maximum value (inclusive)
    :type maxv: int
    :param constant: set to True to exclude parameter from optimisation
    :type constant: bool
    """

    def __init__(self, minv: int, maxv: int,
                 constant: bool = False) -> None:
        """constructor"""
        if not isinstance(minv, int):
            raise TypeError('minv should be an int')
        if not isinstance(maxv, int):
            raise TypeError('maxv should be an int')
        super().__init__(minv, maxv, constant=constant)

    def __repr__(self):
        return f'ParameterInt({self.minv}, {self.maxv}'

    def transform(self, value: int) -> int:
        self.check_value(value)
        return value

    def inv_transform(self, dbval: int) -> int:
        self.check_value(dbval)
        return dbval


class ParameterFloat(Parameter[float]):
    """a float parameter with minimum and maximum value

    :param minv: minimum value (inclusive)
    :type minv: float
    :param maxv: maximum value (inclusive)
    :type maxv: float
    :param resolution: resolution, by default 1e-6
    :type resolution: float
    :param constant: set to True to exclude parameter from optimisation
    :type constant: bool
    """

    def __init__(self, minv: float, maxv: float,
                 resolution: float = 1e-6,
                 constant: bool = False) -> None:
        """constructor"""
        super().__init__(float(minv), float(maxv), constant=constant)
        self._resolution: float = float(resolution)
        # make sure that we can map to integer
        if round((self.maxv - self.minv) / self.resolution) > sys.maxsize - 1:
            raise ValueError("resolution is too fine")

    @property
    def resolution(self) -> float:
        """the resolution used when converting between integer and floats"""
        return self._resolution

    def __repr__(self):
        return f'ParameterFloat({self.minv}, {self.maxv}, ' \
            f'resolution={self.resolution})'

    def check_value(self, value: float) -> None:
        if value < self.minv - 0.99 * self.resolution \
           or value > self.maxv + 0.99 * self.resolution:
            raise ValueError(
                f'value {value} outside bounds [{self.minv}, {self.maxv}]')

    def transform(self, value: float) -> int:
        self.check_value(value)
        return round((value - self.minv) / self.resolution)

    def inv_transform(self, dbval: int) -> float:
        value = self.minv + dbval * self.resolution
        self.check_value(value)
        return value
