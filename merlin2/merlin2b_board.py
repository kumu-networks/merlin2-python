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

    def set_downmixer_iq_compensation(self, gain, phase, input=None):
        """Set downmixer IQ compensation.

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

    def get_downmixer_iq_compensation(self, input):
        """Get downmixer IQ compensation.

        Args:
            input (int): integer in range [0, 1]

        Returns:
            tuple: length 2 tuple of integers (gain, phase)
        """
        if not isinstance(input, int) or input not in (0, 1):
            raise TypeError('input: Expected integer in range [0, 1].')
        downmixer = self.downmixers[input]
        return downmixer.iq_gain_trim, downmixer.iq_phase_trim


class Merlin2bEval(Merlin2bBoard):

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
        )

    def init(self):
        self._miso_en_gpio.set(False)
        self._en_5v_gpio.set(True)
        self._en_3p3v_gpio.set(True)
        self._en_2p5v_gpio.set(True)
        sleep(10e-3)
        super().init()
        for dm in self.downmixers:
            dm.init()


class Merlin2bApp(Merlin2bBoard):

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
        )

    def init(self):
        self._miso_en_gpio.set(False)
        sleep(1e-3)
        super().init()
        for dm in self.downmixers:
            dm.init()
