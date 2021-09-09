__all__ = ['Parameter']


class Parameter:
    """a parameter with minimum and maximum value

    :param minv: minimum value (inclusive)
    :type minv: float
    :param maxv: maximum value (inclusive)
    :type maxv: flat
    :param resolution: resolution, by default 1e-6
    :type resolution: float
    """

    def __init__(self, minv: float, maxv: float,
                 resolution: float = 1e-6) -> None:
        """constructor"""

        self._minv = float(minv)
        self._maxv = float(maxv)
        self._resolution = float(resolution)
        if self.minv >= self.maxv:
            raise ValueError('minv must be smaller than maxv')

    def __repr__(self):
        return f'Parameter({self.minv}, {self.maxv}, ' \
            f'resolution={self.resolution})'

    @property
    def minv(self) -> float:
        """the minimum value the parameter can take"""
        return self._minv

    @property
    def maxv(self) -> float:
        """the maximum value the parameter can take"""
        return self._maxv

    @property
    def resolution(self) -> float:
        """the resolution used when converting between integer and floats"""
        return self._resolution

    def scale(self, value: float) -> float:
        """scale the value to the interval [0,1]

        :param value: value to be scaled
        :type value: float
        """
        if value < self.minv or value > self.maxv:
            raise ValueError(
                f'{value} outside parameter '
                'interval [{self.minv},{self.maxv}]')
        return (value - self.minv) / (self.maxv - self.minv)

    def value(self, scale: float) -> float:
        """convert to value from scaled value

        :param scale: scaled value
        :type scale: float
        """
        if scale < 0 or scale > 1.0:
            raise ValueError(
                f'{scale} outside interval [0,1]')
        return self.minv + scale * (self.maxv - self.minv)

    def scale2int(self, scale: float) -> int:
        """convert scale to integer

        :param scale: scaled value
        :type scale: float
        """
        if scale < 0 or scale > 1.0:
            raise ValueError(
                f'{scale} outside interval [0,1]')
        return round(scale / self.resolution)

    def int2scale(self, iscale: int) -> float:
        """convert integer scale to float

        :param iscale: scaled value
        :type iscale: int
        """
        return iscale * self.resolution

    def value2int(self, value: float) -> int:
        """scale value and convert to integer

        :param value: value to be scaled and converted
        :type value: float
        """
        return self.scale2int(self.scale(value))

    def int2value(self, iscale: int) -> float:
        """convert integer scale to value

        :param iscale: scaled value
        :type iscale: int
        """
        return self.value(self.int2scale(iscale))
