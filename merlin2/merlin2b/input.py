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


class Input(Block):

    VGA_GAIN_TABLE = np.float64([6.92, 4.72, 2.96, 1.50, 0.25, -0.84, -1.81, -2.68])

    @property
    def vga_enable(self):
        """VGA enable.

        Returns:
            bool: enable
        """
        return bool(self.read(0x0, 0, 0x1))

    @vga_enable.setter
    def vga_enable(self, value):
        if not isinstance(value, bool):
            raise ValueError('value: Expected bool.')
        self.write(0x0, value, 0, 0x1)

    @property
    def vga_gain(self):
        """VGA gain in dB.

        Returns:
            float: vga gain in dB
        """
        gains = Input.VGA_GAIN_TABLE
        return float(gains[self.read(0x0, 2, 0x1C)])

    @vga_gain.setter
    def vga_gain(self, gain):
        gains = Input.VGA_GAIN_TABLE
        if not isinstance(gain, (float, int)) or not (min(gains) <= gain <= max(gains)):
            raise TypeError('gain: Expected int / float in range [{}, {}] dB.'.format(
                            min(gains), max(gains)))
        word = int(np.abs(gains - gain).argmin())
        self.write(0x0, word, 2, 0x1C)

    @property
    def vga_gain_table(self):
        """VGA gain table values in dB.

        Returns:
            tuple: tuple of float gain values in dB
        """
        return tuple(float(g) for g in sorted(Input.VGA_GAIN_TABLE))

    @property
    def dc_offset(self):
        """Input I/Q DC offset.

        Returns:
            tuple: length 2 tuple of floats (i, q) in range [-1, +1]
        """
        word = self.read(0x8)
        i = (((word >> 8) & 0x7F) / 127.) * 2. - 1.
        q = (((word >> 16) & 0x7F) / 127.) * 2. - 1.
        return i, q

    @dc_offset.setter
    def dc_offset(self, offsets):
        if not isinstance(offsets, (list, tuple)) or len(offsets) != 2:
            raise TypeError('offsets: Expected list / tuple of length 2.')
        i, q = offsets
        if not isinstance(i, float) or abs(i) > 1.:
            raise ValueError('i: Expected float in range [-1, +1].')
        if not isinstance(q, float) or abs(q) > 1.:
            raise ValueError('q: Expected float in range [-1, +1].')
        i_word = int(round((i + 1.) / 2. * 127))
        q_word = int(round((q + 1.) / 2. * 127))
        self.write(0x8, ((i_word & 0x7F) << 8) | ((q_word & 0x7F) << 16) | 0x3)

    @property
    def pos_gain_trim(self):
        """I/Q positive gain trim.

        Returns:
            tuple: integers (i, q) in range [0, 15]
        """
        word = self.read(0x4)
        i = word & 0xF
        q = (word >> 8) & 0xF
        return i, q

    @pos_gain_trim.setter
    def pos_gain_trim(self, trim):
        if not isinstance(trim, (list, tuple)) or len(trim) != 2:
            raise TypeError('trim: Expected list / tuple of length 2.')
        i, q = trim
        if not isinstance(i, int) or not 0 <= i <= 15:
            raise ValueError('i: Expected integer in range [0, 15].')
        if not isinstance(q, int) or not 0 <= q <= 15:
            raise ValueError('q: Expected integer in range [0, 15].')
        self.write(0x4, i | (q << 8))

    @property
    def neg_gain_trim(self):
        """I/Q negative gain trim.

        Returns:
            tuple: integers (i, q) in range [0, 15]
        """
        word = self.read(0xC)
        i = word & 0xF
        q = (word >> 8) & 0xF
        return i, q

    @neg_gain_trim.setter
    def neg_gain_trim(self, trim):
        if not isinstance(trim, (list, tuple)) or len(trim) != 2:
            raise TypeError('trim: Expected list / tuple of length 2.')
        i, q = trim
        if not isinstance(i, int) or not 0 <= i <= 15:
            raise ValueError('i: Expected integer in range [0, 15].')
        if not isinstance(q, int) or not 0 <= q <= 15:
            raise ValueError('q: Expected integer in range [0, 15].')
        self.write(0xC, i | (q << 8))
