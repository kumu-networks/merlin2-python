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

import unittest
from merlin2 import Merlin2bEval
from test_merlin2b import Merlin2bTestCase
from random import randint


class Merlin2bEvalTestCase(unittest.TestCase, Merlin2bTestCase):

    def setUp(self):
        self._dut = Merlin2bEval()
        self._dut.init()

    def tearDown(self):
        self._dut.init()
        del self._dut

    def test_adc(self):
        value = self._dut.adc.read()
        self.assertIsInstance(value, float)
        self.assertTrue(0 <= value < 1)

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
        }
        readonly = ('chip_id', 'vga_gain_range',)
        self._test_attribute_read_write(self._dut.downmixers, attrs, readonly=readonly)


if __name__ == '__main__':
    unittest.main()
