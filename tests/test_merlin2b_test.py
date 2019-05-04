import unittest
from merlin2 import Merlin2bTest
from test_merlin2b import Merlin2bTestCase
from random import randint


class Merlin2bTestTestCase(unittest.TestCase, Merlin2bTestCase):

    def setUp(self):
        self._dut = Merlin2bTest()
        self._dut.init()

    def tearDown(self):
        self._dut.init()
        del self._dut

    def test_downmixer(self):
        """Test LTC5586 downmixer."""
        for dm in self._dut.downmixers:
            # Initialize downmixer
            dm.init()
            # Reset downmixer
            dm.reset()
            # Test probe
            result = dm.probe()
            self.assertIsInstance(result, bool)
            self.assertTrue(result)
            # Test register read/write
            data = dm.read(0)
            self.assertIsInstance(data, int)
            dm.write(0, data)
        attrs = {
            'vga_im3_trim': (tuple, lambda: tuple(randint(0, 3) for _ in range(2))),
            'vga_gain': (float, lambda: float(randint(0, 7) + 8)),
            'vga_gain_range': (dict,),
            'lo_band': (int, lambda: randint(0, 1)),
            'lo_cf': (tuple, lambda: (randint(0, 31), randint(0, 31))),
            'chip_id': (int, lambda: randint(0, 3)),
            'dc_offset': (tuple, lambda: tuple(randint(0, 255) for _ in range(2))),
            'iq_gain_trim': (int, lambda: randint(0, 63)),
            'hd2_trim': (tuple, lambda: tuple(randint(0, 255) for _ in range(4))),
            'hd3_trim': (tuple, lambda: tuple(randint(0, 255) for _ in range(4))),
            'im2_trim': (tuple, lambda: tuple(randint(0, 255) for _ in range(2))),
            'im3_trim': (tuple, lambda: tuple(randint(0, 255) for _ in range(4))),
            'input_im3_trim': (tuple, lambda: (randint(0, 3), randint(0, 7))),
            'lo_lf': (int, lambda: randint(0, 3)),
            'lo_vcm': (int, lambda: randint(0, 7)),
            'iq_phase_trim': (int, lambda: randint(0, 0x1FF)),
            'input_select': (int, lambda: randint(0, 1)),
            'atten': (float, lambda: float(randint(0, 31))),
        }
        readonly = ('chip_id', 'vga_gain_range',)
        self._test_attribute_read_write(self._dut.downmixers, attrs, readonly=readonly)


if __name__ == '__main__':
    unittest.main()
