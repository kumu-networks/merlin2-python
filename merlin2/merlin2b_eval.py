from .io import Controller
from .ltc55xx import Ltc5586
from .merlin2b import Merlin2b
from time import sleep


class Merlin2bEval(Merlin2b):

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
