"""Copyright (C) Kumu Networks, Inc. All rights reserved.

THIS SOFTWARE IS PROVIDED UNDER A SOFTWARE LICENSE AGREEMENT BY KUMU NETWORKS. BY DOWNLOADING THE
SOFTWARE AND/OR CLICKING THE APPLICABLE BUTTON TO COMPLETE THE INSTALLATION PROCESS, YOU AGREE TO BE
BOUND BY THE TERMS OF THIS AGREEMENT. IF YOU DO NOT WISH TO BECOME A PARTY TO THIS AGREEMENT AND BE
BOUND BY ITS TERMS AND CONDITIONS, DO NOT INSTALL OR USE THE SOFTWARE, AND RETURN THE SOFTWARE
WITHIN THIRTY (30) DAYS OF RECEIPT. ALL RETURNS TO KUMU WILL BE SUBJECT TO KUMU's THEN-CURRENT
RETURN POLICY. IF YOU ARE ACCEPTING THESE TERMS ON BEHALF OF AN ENTITY, YOU AGREE THAT YOU HAVE
AUTHORITY TO BIND THE ENTITY TO THESE TERMS.

THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

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
        weights = np.empty((12, 3), dtype=np.int16)
        for index, word in enumerate(words):
            i = word & 0x1FF
            q = (word >> 9) & 0x1FF
            i = 0x100 - i if i & 0x100 else i
            q = 0x100 - q if q & 0x100 else q
            disconnect = (word >> 28) & 0x1
            weights[index, :] = i, q, disconnect
        return weights
