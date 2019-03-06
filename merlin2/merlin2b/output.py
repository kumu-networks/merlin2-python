from .block import Block


class Output(Block):

    @property
    def dc_offset(self):
        """Output I/Q DC offset.

        Returns:
            tuple: length 2 tuple of floats (i, q) in range [-1, +1]
        """
        word = self.read(0x18)
        i_word = (word >> 8) & 0x7F
        q_word = (word >> 16) & 0x7F
        if self._offset == 0x3040:
            i_word = int('{:07b}'.format(i_word)[::-1], 2)
            q_word = int('{:07b}'.format(q_word)[::-1], 2)
        i = (i_word / 127.) * 2. - 1.
        q = (q_word / 127.) * 2. - 1.
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
        if self._offset == 0x3040:
            i_word = int('{:07b}'.format(i_word)[::-1], 2)
            q_word = int('{:07b}'.format(q_word)[::-1], 2)
        self.write(0x18, ((i_word & 0x7F) << 8) | ((q_word & 0x7F) << 16) | 0x3)
