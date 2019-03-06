from .block import Block
from ..util import issequence


class DelayGroup(Block):

    @property
    def input_select(self):
        """Input select. Can be this Input or other Input for delay chaining.
        NORMAL = 0
        CHAINED = 1

        Returns:
            int: input select in range [0, 1]
        """
        return self.read(0x0, 0, 0x1)

    @input_select.setter
    def input_select(self, value):
        if not isinstance(value, int) or not 0 <= value <= 1:
            raise ValueError('value: Expected integer in range [0, 1].')
        self.write(0x0, value, 0, 0x1)

    @property
    def bandwidth(self):
        """Bandwidth in set {20, 40, 80} MHz in Hz.

        Returns:
            float: bandwidth in Hz
        """
        bandwidths = {0x0: 80.e6, 0x1: 40.e6, 0x3: 20.e6}
        word = self.read(0x4, 0, 0x3)
        return bandwidths[word]

    @bandwidth.setter
    def bandwidth(self, value):
        bandwidths = {80.e6: 0x0, 40.e6: 0x1, 20.e6: 0x3}
        if not isinstance(value, float) or not value in bandwidths:
            raise ValueError('value: Expected float in set {20, 40, 80} MHz.')
        self.write(0x4, bandwidths[value], 0, 0x3)

    @property
    def enable(self):
        """Delay enables. Grouped in 3 tap-groups (1-3, 4-7, 8-11).

        Returns:
            tuple: length 3 tuple of bool's
        """
        word = self.read(0x4)
        return tuple(bool(word & mask) for mask in (0x4, 0x8, 0x10))

    @enable.setter
    def enable(self, values):
        if not isinstance(values, (list, tuple)) or len(values) != 3:
            raise ValueError('values: Expected list/tuple of length 3.')
        if not all(isinstance(value, bool) for value in values):
            raise ValueError('values[i]: Expected bool.')
        word = sum(value << pos for pos, value in enumerate(values))
        self.write(0x4, word, 2, 0x1C)

    @property
    def rc_cal(self):
        """RC calibration setting.

        Returns:
            int: setting in range [0, 31]
        """
        return self.read(0x4, 5, 0x3E0)

    @rc_cal.setter
    def rc_cal(self, value):
        if not isinstance(value, int) or not 0 <= value <= 31:
            raise ValueError('value: Expected integer in range [0, 31].')
        self.write(0x4, value, 5, 0x3E0)

    @property
    def gains(self):
        """Delay gain control.

        Returns:
            tuple: length 11 tuple of float's in dB
        """
        low_delays = {0: -4., 1: -2., 2: 0.}
        high_delays = {0: -2., 1: 0., 2: 2.}
        return tuple(low_delays[self.read(0x8 + t * 4)] for t in range(2)) \
             + tuple(high_delays[self.read(0x8 + t * 4)] for t in range(2, 11))

    @gains.setter
    def gains(self, gains):
        if not issequence(gains) or len(gains) != 11:
            raise TypeError('gains: Expected sequence of length 11.')
        low_delays = {-4: 0, -2: 1, 0: 2}
        high_delays = {-2: 0, 0: 1, 2: 2}
        if not all(isinstance(i, (float, int)) and i in low_delays for i in gains[:2]):
            raise ValueError('gains[0..1]: Expected float / integer in set {-4, -2, 0} dB.')
        if not all(isinstance(i, (float, int)) and i in high_delays for i in gains[2:]):
            raise ValueError('gains[2..10]: Expected float / integer in set {-2, 0, 2} dB.')
        for index, value in enumerate(gains):
            word = low_delays[value] if index < 2 else high_delays[value]
            self.write(0x8 + index * 4, word, 0, 0x3)
