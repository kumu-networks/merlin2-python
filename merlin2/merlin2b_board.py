"""Copyright (C) Kumu Networks, Inc. All rights reserved.

THIS SOFTWARE IS PROVIDED UNDER A SOFTWARE LICENSE AGREEMENT BY KUMU NETWORKS. BY DOWNLOADING THE
SOFTWARE AND/OR CLICKING THE APPLICABLE BUTTON TO COMPLETE THE INSTALLATION PROCESS, YOU AGREE TO BE
BOUND BY THE TERMS OF THIS AGREEMENT. IF YOU DO NOT WISH TO BECOME A PARTY TO THIS AGREEMENT AND BE
BOUND BY ITS TERMS AND CONDITIONS, DO NOT INSTALL OR USE THE SOFTWARE, AND RETURN THE SOFTWARE
WITHIN THIRTY (30) DAYS OF RECEIPT. ALL RETURNS TO KUMU WILL BE SUBJECT TO KUMU’s THEN-CURRENT
RETURN POLICY. IF YOU ARE ACCEPTING THESE TERMS ON BEHALF OF AN ENTITY, YOU AGREE THAT YOU HAVE
AUTHORITY TO BIND THE ENTITY TO THESE TERMS.

THIS SOFTWARE IS PROVIDED “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

from .io import Controller
from .ltc55xx import Ltc5586, Ltc5594
from .ads7866 import Ads7866
from .merlin2b import Merlin2b
from time import sleep


class Merlin2bBoard(Merlin2b):

    def probe(self):
        """Probe for board. This will test SPI communication to all ICs.

        Returns:
            bool: result
        """
        if not super().probe():
            return False
        for dm in self.downmixers:
            if not dm.probe():
                return False
        return True

    def setup(self, num_input, num_output, bandwidth, lo_freq, chain=False):
        """Setup board.

        Args:
            num_input (int): number of inputs, integer in range [1...2]
            num_output (int): number of outputs, integer in range [1...2]
            bandwidth (float): bandwidth in Hz, float in set {20e6, 40e6, 80e6}
            lo_freq (float, str): LO frequency in Hz or 'default'
            chain (bool, optional): chain multiple filters, default False.
        """
        super().setup(num_input, num_output, bandwidth, chain=chain)
        for dm in self.downmixers:
            dm.setup(lo_freq)

    @property
    def serial_number(self):
        """Serial number.

        Returns:
            str: serial number
        """
        return self._io.serial_number

    def set_downmixer_gain(self, gain, input=None):
        """Set downmixer gain.

        Args:
            gain (float): gain setting in dB in range [8, 15]
            input (int, optional): integer in range [0, 1]
        """
        if input is None:
            for inp in self.downmixers:
                inp.vga_gain = gain
        elif isinstance(input, int) and input in (0, 1):
            self.downmixers[input].vga_gain = gain
        else:
            raise TypeError('input: Expected integer in range [0, 1].')

    def get_downmixer_gain(self, input=None):
        """Get downmixer gain.

        Args:
            input (int, optional): integer in range [0, 1]

        Returns:
            tuple or float: tuple of floats or float gain in dB
        """
        if input is None:
            return tuple(inp.vga_gain for inp in self.downmixers)
        elif isinstance(input, int) and input in (0, 1):
            return self.downmixers[input].vga_gain
        raise TypeError('input: Expected integer in range [0, 1].')

    def get_downmixer_gain_range(self):
        """Downmixer gain range.

        Returns:
            dict: range in dB
        """
        return self.downmixers[0].vga_gain_range

    def set_downmixer_iq_correction(self, gain, phase, input=None):
        """Set downmixer IQ correction.

        Args:
            gain (int): gain in range [0, 0x3F]
            phase (int): phase in range [0, 0x1FF]
            input (int, optional): integer in range [0, 1]
        """
        if input is None:
            for downmixer in self.downmixers:
                downmixer.iq_gain_trim = gain
                downmixer.iq_phase_trim = phase
        elif isinstance(input, int) and input in (0, 1):
            downmixer = self.downmixers[input]
            downmixer.iq_gain_trim = gain
            downmixer.iq_phase_trim = phase
        else:
            raise TypeError('input: Expected integer in range [0, 1].')

    def get_downmixer_iq_correction(self, input):
        """Get downmixer IQ correction.

        Args:
            input (int): integer in range [0, 1]

        Returns:
            tuple: length 2 tuple of integers (gain, phase)
        """
        if not isinstance(input, int) or input not in (0, 1):
            raise TypeError('input: Expected integer in range [0, 1].')
        downmixer = self.downmixers[input]
        return downmixer.iq_gain_trim, downmixer.iq_phase_trim

    def set_downmixer_im2_correction(self, i, q, input=None):
        """Set downmixer IM2 correction.

        Args:
            i (int): i value in range [0, 255]
            q (int): q value in range [0, 255]
            input (int, optional): integer in range [0, 1]
        """
        if input is None:
            for downmixer in self.downmixers:
                downmixer.im2_trim = (i, q)
        elif isinstance(input, int) and input in (0, 1):
            downmixer = self.downmixers[input]
            downmixer.im2_trim = (i, q)
        else:
            raise TypeError('input: Expected integer in range [0, 1].')

    def get_downmixer_im2_correction(self, input):
        """Get downmixer IM2 correction.

        Args:
            input (int): integer in range [0, 1]

        Returns:
            tuple: length 2 tuple of integers (i, q)
        """
        if not isinstance(input, int) or input not in (0, 1):
            raise TypeError('input: Expected integer in range [0, 1].')
        downmixer = self.downmixers[input]
        return downmixer.im2_trim

    def set_downmixer_dc_offset(self, i_offset, q_offset, input=None):
        """Set downmixer DC offset.

        Args:
            i_offset (float): I DC offset in range [-1, +1]
            q_offset (float): Q DC offset in range [-1, +1]
            input (int, optional): integer in range [0, 1]

        Returns:
            tuple: length 2 tuple of floats (i, q) in range [-1, +1]
        """
        if not isinstance(i_offset, float) or abs(i_offset) > 1.:
            raise ValueError('i_offset: Expected float in range [-1, +1].')
        if not isinstance(q_offset, float) or abs(q_offset) > 1.:
            raise ValueError('q_offset: Expected float in range [-1, +1].')
        i_word = min(max(int(round((i_offset + 1.) * 128.)), 0), 255)
        q_word = min(max(int(round((q_offset + 1.) * 128.)), 0), 255)
        if input is None:
            for input in range(2):
                self.downmixers[input].dc_offset = (i_word, q_word)
        elif isinstance(input, int) and input in (0, 1):
            self.downmixers[input].dc_offset = (i_word, q_word)
        else:
            raise TypeError('input: Expected integer in range [0, 1].')
        i_word, q_word = self.downmixers[input].dc_offset
        i_actual = (i_word / 128.) - 1.
        q_actual = (q_word / 128.) - 1.
        return i_actual, q_actual

    def get_downmixer_dc_offset(self, input):
        """Get downmixer DC offset.

        Args:
            input (int): integer in range [0, 1]

        Returns:
            tuple: length 2 tuple of floats (i, q) in range [-1, +1]
        """
        if not isinstance(input, int) or input not in (0, 1):
            raise TypeError('input: Expected integer in range [0, 1].')
        i_word, q_word = self.downmixers[input].dc_offset
        i_offset = (i_word / 128.) - 1.
        q_offset = (q_word / 128.) - 1.
        return i_offset, q_offset


class Merlin2bTest(Merlin2bBoard):

    def __init__(self, serial_number=None):
        if serial_number is not None and not isinstance(serial_number, str):
            raise TypeError('serial_number: Expected str.')
        self._io = Controller(serial_number=serial_number)
        self._en_5v_gpio = self._io.get_gpio(11, direction='output', active_low=False)
        self._en_3p3v_gpio = self._io.get_gpio(12, direction='output', active_low=False)
        self._en_2p5v_gpio = self._io.get_gpio(7, direction='output', active_low=False)
        self._miso_en_gpio = self._io.get_gpio(10, direction='output', active_low=True)
        # Create downmixers
        self.downmixers = []
        for index in range(2):
            dm = Ltc5586(self._io.get_spi(cs=index, freq_hz=1e6, mode=0,
                                          miso_en_gpio=self._miso_en_gpio))
            self.downmixers.append(dm)
        # Create merlin
        super().__init__(
            self._io.get_spi(cs=2, freq_hz=1e6, mode=0),
            self._io.get_gpio(8, direction='output', active_low=True),
            self._io.get_gpio(9, direction='output', active_low=False),
            use_vga=True,
        )

    def init(self):
        """Initialize board."""
        self._miso_en_gpio.set(False)
        self._en_5v_gpio.set(True)
        self._en_3p3v_gpio.set(True)
        self._en_2p5v_gpio.set(True)
        sleep(10e-3)
        super().init()
        for dm in self.downmixers:
            dm.init()


class Merlin2bEval(Merlin2bBoard):

    def __init__(self, serial_number=None):
        if serial_number is not None and not isinstance(serial_number, str):
            raise TypeError('serial_number: Expected str.')
        self._io = Controller(serial_number=serial_number)
        self._miso_en_gpio = self._io.get_gpio(10, direction='output', active_low=True)
        # Create downmixers
        self.downmixers = []
        for index in range(2):
            dm = Ltc5594(self._io.get_spi(cs=index, freq_hz=1e6, mode=0,
                                          miso_en_gpio=self._miso_en_gpio))
            self.downmixers.append(dm)
        # Create ADC
        self.adc = Ads7866(self._io.get_spi(cs=3, freq_hz=1e6, mode=0,
                                            miso_en_gpio=self._miso_en_gpio))
        # Create merlin
        super().__init__(
            self._io.get_spi(cs=2, freq_hz=1e6, mode=0),
            self._io.get_gpio(8, direction='output', active_low=True),
            self._io.get_gpio(9, direction='output', active_low=False),
            use_vga=False,
        )

    def init(self):
        """Initialize board."""
        self._miso_en_gpio.set(False)
        sleep(1e-3)
        super().init()
        for dm in self.downmixers:
            dm.init()
