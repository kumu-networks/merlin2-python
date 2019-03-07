import unittest
from merlin2 import Merlin2bEval
from random import randint, shuffle, sample, choice, uniform
from functools import partial
import numpy as np


class Merlin2bEvalTestCase(unittest.TestCase):

    def setUp(self):
        self._dut = Merlin2bEval()
        self._dut.init()

    def tearDown(self):
        self._dut.init()
        del self._dut

    def test_top(self):
        self._dut.init()
        self._dut.reset()
        self._dut.apply()

        # probe()
        ret = self._dut.probe()
        self.assertIsInstance(ret, bool)
        self.assertTrue(ret)

        # setup()
        for num_input in (1, 2):
            for num_output in (1, 2):
                for bandwidth in (20e6, 40e6, 80e6):
                    for chain in (True, False):
                        for lo_freq in (1500e6, 2400e6, 3500e6):
                            if chain and num_input > 1:
                                continue
                            self._dut.setup(num_input, num_output, bandwidth,
                                            lo_freq, chain=chain)

        # serial_number
        ret = self._dut.serial_number
        self.assertIsInstance(ret, str)

        # set/get_vga_gain
        vga_gain_table = self._dut.get_vga_gain_table()
        self.assertIsInstance(vga_gain_table, tuple)
        self.assertTrue(all(isinstance(g, float) for g in vga_gain_table))
        values = {}
        for it in range(100):
            # Write gain
            for input in sample((None, 0, 1), k=3):
                # If input is None, both VGA gains will be set
                wdata = choice(vga_gain_table)
                self._dut.set_vga_gain(wdata, input=input)
                if input is None:
                    for index in range(2):
                        values[index] = wdata
                else:
                    values[input] = wdata
            # Read gain
            for input in sample((None, 0, 1), k=3):
                rdata = self._dut.get_vga_gain(input=input)
                if input is None:
                    self.assertIsInstance(rdata, tuple)
                    self.assertTrue(all(isinstance(g, float) for g in rdata))
                    self.assertTrue(len(rdata) == 2)
                    self.assertEqual(rdata, tuple(values[i] for i in range(2)))
                else:
                    self.assertIsInstance(rdata, float)
                    self.assertEqual(rdata, values[input])

        # set/get_downmixer_gain
        downmixer_gain_range = self._dut.get_downmixer_gain_range()
        self.assertIsInstance(downmixer_gain_range, dict)
        self.assertEqual(len(downmixer_gain_range), 3)
        self.assertTrue(all(isinstance(downmixer_gain_range[k], float) \
                            for k in ('start', 'stop', 'step')))
        values = {}
        for it in range(100):
            # Write gain
            for input in sample((None, 0, 1), k=3):
                # If input is None, both VGA gains will be set
                wdata = float(randint(0, 7) + 8)
                self._dut.set_downmixer_gain(wdata, input=input)
                if input is None:
                    for index in range(2):
                        values[index] = wdata
                else:
                    values[input] = wdata
            # Read gain
            for input in sample((None, 0, 1), k=3):
                rdata = self._dut.get_downmixer_gain(input=input)
                if input is None:
                    self.assertIsInstance(rdata, tuple)
                    self.assertTrue(all(isinstance(g, float) for g in rdata))
                    self.assertTrue(len(rdata) == 2)
                    self.assertEqual(rdata, tuple(values[i] for i in range(2)))
                else:
                    self.assertIsInstance(rdata, float)
                    self.assertEqual(rdata, values[input])

        # set/get_weights
        for chain in (True, False):
            self._dut.setup(2, 2, 80e6, 1700e6, chain=chain)
            num_taps = 23 if chain else 12
            num_filters = 2 if chain else 4
            for it in range(100):
                wdata = (np.random.rand(num_taps, num_filters) * 2 - 1) + \
                        1j * (np.random.rand(num_taps, num_filters) * 2 - 1)
                mapped = self._dut.set_weights(wdata)
                rdata = self._dut.get_weights()
                self.assertIsInstance(mapped, np.ndarray)
                self.assertTrue(mapped.shape == (num_taps, num_filters))
                self.assertTrue(mapped.dtype == np.complex128)
                self.assertIsInstance(rdata, np.ndarray)
                self.assertTrue(rdata.shape == (num_taps, num_filters))
                self.assertTrue(rdata.dtype == np.complex128)
                self.assertTrue(np.array_equal(rdata, mapped))
                error = 20 * np.log10(np.max(np.abs(wdata - rdata)))
                self.assertLess(error, -50) # This error ought to be less than 50 dB

    def test_filter(self):
        """Test Merlin2b filter."""
        attrs = {
            'enable': (bool, lambda: bool(randint(0, 1))),
            'summer_enable': (bool, lambda: bool(randint(0, 1))),
            'tap_bypass': (bool, lambda: bool(randint(0, 1))),
        }
        # Flatten filters
        filters = [item for sublist in self._dut.filters for item in sublist]
        self._test_attribute_read_write(filters, attrs)
        values = {}
        for it in range(100):
            # Write weights
            for index in sample(range(len(filters)), k=len(filters)):
                wdata = np.empty((12, 3), dtype=np.int16)
                wdata[:,:2] = np.random.randint(-255, 256, size=(12, 2), dtype=np.int16)
                wdata[:,2] = np.random.randint(0, 2, size=(12,), dtype=np.int16)
                filters[index].set_weights(wdata)
                values[index] = wdata
            # Read weights
            for index in sample(range(len(filters)), k=len(filters)):
                rdata = filters[index].get_weights()
                self.assertIsInstance(rdata, np.ndarray)
                self.assertTrue(rdata.shape == (12, 3))
                self.assertTrue(rdata.dtype == np.int16)
                self.assertTrue(np.array_equal(rdata, values[index]))

    def test_summer(self):
        """Test Merlin2b Summer."""
        attrs = {
            'enable': (bool, lambda: bool(randint(0, 1))),
        }
        self._test_attribute_read_write(self._dut.summers, attrs)

    def test_input(self):
        """Test Merlin2b Input."""
        VGA_GAIN_TABLE = self._dut.inputs[0].vga_gain_table
        attrs = {
            'vga_enable': (bool, lambda: bool(randint(0, 1))),
            'vga_gain': (float, partial(choice, VGA_GAIN_TABLE)),
            'dc_offset': (tuple, lambda: tuple((randint(0, 127) / 127 * 2 - 1) for _ in range(2))),
            'pos_gain_trim': (tuple, lambda: tuple(randint(0, 15) for _ in range(2))),
            'neg_gain_trim': (tuple, lambda: tuple(randint(0, 15) for _ in range(2))),
        }
        self._test_attribute_read_write(self._dut.inputs, attrs)

    def test_output(self):
        """Test Merlin2b Output."""
        attrs = {
            'dc_offset': (tuple, lambda: tuple((randint(0, 127) / 127 * 2 - 1) for _ in range(2))),
        }
        self._test_attribute_read_write(self._dut.outputs, attrs)

    def test_delaygroup(self):
        """Test Merlin2b DelayGroup."""
        low_gains = (-4., -2., 0.)
        high_gains = (-2., 0., 2.)
        attrs = {
            'input_select': (int, partial(randint, 0, 1)),
            'bandwidth': (float, lambda: choice((20e6, 40e6, 80e6))),
            'enable': (tuple, lambda: tuple(bool(randint(0, 1)) for _ in range(3))),
            'rc_cal': (int, partial(randint, 0, 31)),
            'gains': (tuple, lambda: tuple(choice(low_gains) for _ in range(2)) + \
                                     tuple(choice(high_gains) for _ in range(9))),

        }
        self._test_attribute_read_write(self._dut.delays, attrs)

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

    def _test_attribute_read_write(self, objects, attrs, readonly=(), num_iter=100):
        values = [{} for _ in range(len(objects))]
        for index, dm in enumerate(objects):
            for key, value in attrs.items():
                values[index][key] = getattr(dm, key)
        for it in range(num_iter):
            # Write
            keys = list(k for k in attrs.keys() if k not in readonly)
            shuffle(keys)
            for key in keys:
                index = randint(0, 1)
                wdata = attrs[key][1]()
                values[index][key] = wdata
                print('write \'{}\' to \'{}\' @ {}.'.format(wdata, key, index))
                setattr(objects[index], key, wdata)
            # Read
            keys = list(attrs.keys())
            shuffle(keys)
            for key in keys:
                for index in sample(range(2), k=2):
                    rdata = getattr(objects[index], key)
                    print('read \'{}\' from \'{}\' @ {}.'.format(rdata, key, index))
                    self.assertIsInstance(rdata, attrs[key][0])
                    wdata = values[index][key]
                    self.assertEqual(wdata, rdata, 'index = {}, attribute = {}, got = {},' \
                                     ' expected = {}'.format(index, key, rdata, wdata))


if __name__ == '__main__':
    unittest.main()
