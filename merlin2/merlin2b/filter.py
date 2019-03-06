import numpy as np

from .block import Block


class Filter(Block):

    @property
    def enable(self):
        """Enable filter.

        Returns:
            bool: enable
        """
        return bool(self.read(0x0, 0, 0x1))

    @enable.setter
    def enable(self, value):
        if not isinstance(value, bool):
            raise ValueError('value: Expected bool.')
        self.write(0x0, value, 0, 0x1)

    @property
    def summer_enable(self):
        """Enable 1st stage summer.

        Returns:
            bool: enable
        """
        return bool(not self.read(0x0, 1, 0x2))

    @summer_enable.setter
    def summer_enable(self, value):
        if not isinstance(value, bool):
            raise ValueError('value: Expected bool.')
        self.write(0x0, not value, 1, 0x2)

    @property
    def tap_bypass(self):
        """Tap 1 1st stage summer bypass.

        Returns:
            bool: bypass
        """
        return bool(self.read(0x0, 2, 0x1C))

    @tap_bypass.setter
    def tap_bypass(self, bypass):
        if not isinstance(bypass, bool):
            raise ValueError('bypass: Expected bool.')
        self.write(0x0, 0x7 if bypass else 0x0, 2, 0x1C)

    def set_weights(self, weights):
        if not isinstance(weights, np.ndarray) or weights.shape != (12, 3) \
          or weights.dtype != np.int16:
            raise TypeError('weights: Expected ndarray of size (12, 3) of type int16.')
        if (abs(weights[:, :2]) > 255).any():
            raise ValueError('weights[:, 0:2]: Out-of-range, must be [-255, 255].')
        if (weights[:, 2] < 0).any() or (weights[:, 2] > 1).any():
            raise ValueError('weights[:, 2]: Must be integer in set {0, 1}.')
        words = []
        for index in range(12):
            i, q, disconnect = weights[index, :]
            i = int(i if i >= 0 else abs(i) + 0x100)
            q = int(q if q >= 0 else abs(q) + 0x100)
            words.append(i | q << 9 | int(disconnect) << 28)
        self.write(0x4, words)

    def get_weights(self):
        words = self.read(0x4, length=12)
        weights = np.empty((12, 2), dtype=np.int16)
        for index, word in enumerate(words):
            i = word & 0x1FF
            q = (word >> 9) & 0x1FF
            i = 0x100 - i if i & 0x100 else i
            q = 0x100 - q if q & 0x100 else q
            weights[index, :] = i, q
        return weights