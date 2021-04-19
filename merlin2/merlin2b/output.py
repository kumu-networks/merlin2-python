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
