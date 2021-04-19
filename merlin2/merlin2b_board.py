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

from .io import Controller
from .ltc55xx import Ltc5586, Ltc5594
from .ads7866 import Ads7866
from .merlin2b import Merlin2b
from time import sleep


class Merlin2bBoard:

    def init(self):
        """Initialize board."""
        try:
            self.ic.init()
        except Exception as e:
            raise RuntimeError('Failed to initialize IC.') from e
        for index, dm in enumerate(self.downmixers):
            try:
                dm.init()
            except Exception as e:
                raise RuntimeError('Failed to initialize downmixer {}.'.format(index)) from e

    def reset(self):
        """Reset board."""
        self.ic.reset()
        for dm in self.downmixers:
            dm.reset()

    def probe(self):
        """Probe for board. This will test SPI communication to all ICs.

        Returns:
            bool: result
        """
        if not self.ic.probe():
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
        self.ic.setup(num_input, num_output, bandwidth, chain=chain)
        for dm in self.downmixers:
            dm.setup(lo_freq)

    def apply(self):
        """Apply weights by toggling APLS pin."""
        self.ic.apply()

    def set_vga_gain(self, *args, **kwargs):
        """Set VGA gain.

        Args:
            gain (float): gain setting in range [-2.68, 6.92]
            input (int, optional): integer in range [0, 1]
        """
        return self.ic.set_vga_gain(*args, **kwargs)

    def get_vga_gain(self, *args, **kwargs):
        """Get VGA gain.

        Args:
            input (int, optional): integer in range [0, 1]

        Returns:
            tuple or float: tuple of floats or float gain in dB
        """
        return self.ic.get_vga_gain(*args, **kwargs)

    def get_vga_gain_table(self, *args, **kwargs):
        """VGA gain table.

        Returns:
            tuple: tuple of floats, gain in dB
        """
        return self.ic.get_vga_gain_table(*args, **kwargs)

    def set_gain_profile(self, *args, **kwargs):
        """Set gain-delay profile.

        Args:
            gains (sequence): sequence of gains in dB of length 11 or 22
        """
        return self.ic.set_gain_profile(*args, **kwargs)

    def get_gain_profile(self, *args, **kwargs):
        """Get gain-delay profile.

        Returns:
            tuple: tuple of float gains in dB
        """
        return self.ic.get_gain_profile(*args, **kwargs)

    def set_input_dc_offset(self, *args, **kwargs):
        """Set input DC offset.

        Args:
            i_offset (float): I DC offset in range [-1, +1]
            q_offset (float): Q DC offset in range [-1, +1]
            input (int, optional): integer in range [0, 1]

        Returns:
            tuple: length 2 tuple of floats (i, q) in range [-1, +1]
        """
        return self.ic.set_input_dc_offset(*args, **kwargs)

    def get_input_dc_offset(self, *args, **kwargs):
        """Get input DC offset.

        Args:
            input (int): integer in range [0, 1]

        Returns:
            tuple: length 2 tuple of floats (i, q) in range [-1, +1]
        """
        return self.ic.get_input_dc_offset(*args, **kwargs)

    def set_output_dc_offset(self, *args, **kwargs):
        """Set output DC offset.

        Args:
            i_offset (float): I DC offset in range [-1, +1]
            q_offset (float): Q DC offset in range [-1, +1]
            output (int, optional): integer in range [0, 1]

        Returns:
            tuple: length 2 tuple of floats (i, q) in range [-1, +1]
        """
        return self.ic.set_output_dc_offset(*args, **kwargs)

    def get_output_dc_offset(self, *args, **kwargs):
        """Get output DC offset.

        Args:
            output (int): integer in range [0, 1]

        Returns:
            tuple: length 2 tuple of floats (i, q) in range [-1, +1]
        """
        return self.ic.get_output_dc_offset(*args, **kwargs)

    def set_weights(self, *args, **kwargs):
        """Set weights.

        Args:
            weights (ndarray): ndarray of shape (12, 4) if not chained, else
                               of shape (23, 2)
            apply (bool, optional): apply weights to filter

        Returns:
            ndarray: mapped weights
        """
        return self.ic.set_weights(*args, **kwargs)

    def get_weights(self):
        """Get weights.

        Returns:
            ndarray: ndarray of shape (12, 4) if not chained, else
                     of shape (23, 2)
        """
        return self.ic.get_weights()

    def clear_weights(self, *args, **kwargs):
        """Clear weights.

        Args:
            apply (bool, optional): apply weights to filter

        Returns:
            ndarray: ndarray of shape (12, 4) if not chained, else
                     of shape (23, 2)
        """
        return self.ic.clear_weights(*args, **kwargs)

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

    def __init__(self, serial_number=None, chip_revision=2):
        if serial_number is not None and not isinstance(serial_number, str):
            raise TypeError('serial_number: Expected str.')
        self._io = Controller(cs_count=3, serial_number=serial_number)
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
        self.ic = Merlin2b(
            self._io.get_spi(cs=2, freq_hz=1e6, mode=0),
            self._io.get_gpio(8, direction='output', active_low=True),
            self._io.get_gpio(9, direction='output', active_low=False),
            use_vga=True, revision=chip_revision,
        )

    def init(self):
        """Initialize board."""
        self._miso_en_gpio.set(False)
        self._en_5v_gpio.set(True)
        self._en_3p3v_gpio.set(True)
        self._en_2p5v_gpio.set(True)
        sleep(10e-3)
        super().init()


class Merlin2bEval(Merlin2bBoard):

    def __init__(self, serial_number=None, chip_revision=2):
        if serial_number is not None and not isinstance(serial_number, str):
            raise TypeError('serial_number: Expected str.')
        self._io = Controller(cs_count=4, serial_number=serial_number)
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
        self.ic = Merlin2b(
            self._io.get_spi(cs=2, freq_hz=1e6, mode=0),
            self._io.get_gpio(8, direction='output', active_low=True),
            self._io.get_gpio(9, direction='output', active_low=False),
            use_vga=False, revision=chip_revision,
        )

    def init(self):
        """Initialize board."""
        self._miso_en_gpio.set(False)
        sleep(1e-3)
        super().init()
