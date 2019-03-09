"""Driver for ADS7866, 12-bit ADC."""

class Ads7866:

    def __init__(self, interface):
        self._iface = interface

    def read(self):
        """Make ADC measurement.

        Returns:
            float: measurement normalized to [0, 1).
        """
        rdata = self._iface.read(readlen=2)
        word = ((rdata[0] << 8) | rdata[1]) & 0xFFF
        return (word / 4096)
