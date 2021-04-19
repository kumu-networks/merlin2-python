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


class Ltc5594:
    """Driver for LTC5586/94 I/Q demodulator."""

    # Register settings for single-ended LO matching
    LO_TABLE = {
        'default': (1, 8, 3, 3),
        (300, 339): (0, 31, 3, 31),
        (339, 398): (0, 21, 3, 24),
        (398, 419): (0, 14, 3, 23),
        (419, 556): (0, 17, 2, 31),
        (556, 625): (0, 10, 2, 23),
        (625, 801): (0, 15, 1, 31),
        (801, 831): (0, 14, 1, 27),
        (831, 1046): (0, 8, 1, 21),
        (1046, 1242): (1, 31, 3, 31),
        (1242, 1411): (1, 21, 3, 28),
        (1411, 1696): (1, 17, 2, 26),
        (1696, 2070): (1, 15, 1, 31),
        (2070, 2470): (1, 8, 1, 21),
        (2470, 2980): (1, 2, 1, 10),
        (2980, 3500): (1, 1, 0, 19),
        (3500, 9000): (1, 0, 0, 0),
    }

    def __init__(self, interface):
        self._iface = interface

    def init(self):
        """Initialize device."""
        self.reset()
        if not self.probe():
            raise RuntimeError('Probe failed.')

    def probe(self):
        """Probe for device.

        Returns:
            bool: probe result
        """
        data = self.read(0x16)
        return data == 0xF0

    def setup(self, lo_freq):
        """Setup downmixer.

        Args:
            lo_freq (float, int, str): LO frequency in Hz or 'default'
        """
        self.init()
        if isinstance(lo_freq, (float, int)):
            freq_mhz = lo_freq / 1e6
            for freqs, words in Ltc5594.LO_TABLE.items():
                if isinstance(freqs, tuple) and freqs[0] <= freq_mhz <= freqs[1]:
                    band, cf1, lf1, cf2 = words
                    break
            else:
                raise RuntimeError('Failed to match LO frequency to band.')
        elif lo_freq == 'default':
            band, cf1, lf1, cf2 = Ltc5594.LO_TABLE['default']
        else:
            raise TypeError('lo_freq: Expected float, int or \'default\'.')
        self.lo_band = band
        self.lo_cf = (cf1, cf2)
        self.lo_lf = lf1

    @property
    def vga_im3_trim(self):
        """Used to optimize the IF amplifier IM3.

        Returns:
            tuple: integers (cc, ic) in range [0, 3]
        """
        data = self._read(0x15, 0, 0xF)
        return ((data & 0x0C) >> 2, data & 0x03)

    @vga_im3_trim.setter
    def vga_im3_trim(self, trim):
        if not isinstance(trim, (list, tuple)) or len(trim) != 2:
            raise TypeError('trim: Expected list / tuple of length 2.')
        cc, ic = trim
        if not isinstance(cc, int) or not 0 <= cc <= 3:
            raise ValueError('cc: Expected integer in range [0, 3].')
        if not isinstance(ic, int) or not 0 <= ic <= 3:
            raise ValueError('ic: Expected integer in range [0, 3].')
        word = (cc << 2) | ic
        self._write(0x15, word, 0, 0xF)

    @property
    def vga_gain(self):
        """Adjusts the amplifier gain from 8 to 15 dB.

        Returns:
            float: gain in range [8, 15] dB
        """
        return float(self._read(0x15, 4, 0x70) + 8)

    @vga_gain.setter
    def vga_gain(self, gain):
        if not isinstance(gain, (float, int)) or not 8. <= gain <= 15.:
            raise ValueError('gain: Expected float or integer in range [8, 15] dB.')
        self._write(0x15, int(round(gain - 8.)), 4, 0x70)

    @property
    def vga_gain_range(self):
        """VGA gain range in dB.

        Returns:
            dict: range
        """
        return {'start': 8., 'stop': 15., 'step': 1.}

    @property
    def lo_band(self):
        """Selects which LO matching band is used. BAND = 1 for high band. BAND = 0 for low band.

        Returns:
            int: band, integer in range [0, 1]
        """
        return self._read(0x13, 7, 0x80)

    @lo_band.setter
    def lo_band(self, band):
        if not isinstance(band, int) or not 0 <= band <= 1:
            raise ValueError('band: Expected integer in range [0, 1].')
        self._write(0x13, band, 7, 0x80)

    @property
    def lo_cf(self):
        """Controls the CF1 / CF2 capacitors in the LO matching network.

        Returns:
            tuple: integers (cf1, cf2) in range [0, 0x1F]
        """
        cf1 = self._read(0x12, 0, 0x1F)
        cf2 = self._read(0x13, 0, 0x1F)
        return (cf1, cf2)

    @lo_cf.setter
    def lo_cf(self, values):
        if not isinstance(values, (list, tuple)) or len(values) != 2:
            raise TypeError('values: Expected list / tuple of length 2.')
        cf1, cf2 = values
        if not isinstance(cf1, int) or not 0 <= cf1 <= 31:
            raise ValueError('cf1: Expected integer in range [0, 31].')
        if not isinstance(cf2, int) or not 0 <= cf2 <= 31:
            raise ValueError('cf2: Expected integer in range [0, 31].')
        self._write(0x12, cf1, 0, 0x1F)
        self._write(0x13, cf2, 0, 0x1F)

    @property
    def chip_id(self):
        """Chip identification bits.

        Returns:
            int: chip-id, integer in range [0, 3]
        """
        return self._read(0x17, 2, 0xC0)

    @chip_id.setter
    def chip_id(self, value):
        if not isinstance(value, int) or not 0 <= value <= 3:
            raise ValueError('value: Expected integer in range [0, 3].')
        self._write(0x17, value, 2, 0xC0)

    @property
    def dc_offset(self):
        """I/Q DC offset over a range from -200mV to 200mV.

        Returns:
            tuple: integers (i, q) in range [0, 255]
        """
        return self._read(0x0E, 0, 0xFF), self._read(0x0F, 0, 0xFF)

    @dc_offset.setter
    def dc_offset(self, offsets):
        if not isinstance(offsets, (list, tuple)) or len(offsets) != 2:
            raise TypeError('offsets: Expected list / tuple of length 2.')
        i, q = offsets
        if not isinstance(i, int) or not 0 <= i <= 255:
            raise ValueError('i: Expected integer in range [0, 255].')
        if not isinstance(q, int) or not 0 <= q <= 255:
            raise ValueError('q: Expected integer in range [0, 255].')
        self._write(0x0E, i, 0, 0xFF)
        self._write(0x0F, q, 0, 0xFF)

    @property
    def iq_gain_trim(self):
        """Controls the IQ gain trim over a range from -0.5 to 0.5 dB.

        Returns:
            int: integer in range [0, 63]
        """
        return self._read(0x11, 2, 0xFC)

    @iq_gain_trim.setter
    def iq_gain_trim(self, trim):
        if not isinstance(trim, int) or not 0 <= trim <= 63:
            raise ValueError('trim: Expected integer in range [0, 63].')
        self._write(0x11, trim, 2, 0xFC)

    @property
    def hd2_trim(self):
        """Controls the I/Q-channel HD2 X/Y-vector trim.

        Returns:
            tuple: integers (ix, iy, qx, qy) in range [0, 255]
        """
        return tuple(self._read(addr, 0, 0xFF) for addr in (0x0D, 0x0C, 0x0B, 0x0A))

    @hd2_trim.setter
    def hd2_trim(self, values):
        if not isinstance(values, (list, tuple)) or len(values) != 4:
            raise TypeError('values: Expected list / tuple of length 4.')
        if any(not isinstance(i, int) or not 0 <= i <= 255 for i in values):
            raise ValueError('values[i]: Expected integer in range [0, 255].')
        for addr, value in zip((0x0D, 0x0C, 0x0B, 0x0A), values):
            self._write(addr, value, 0, 0xFF)

    @property
    def hd3_trim(self):
        """Controls the I/Q-channel HD3 X/Y-vector trim.

        Returns:
            tuple: integers (ix, iy, qx, qy) in range [0, 255]
        """
        return tuple(self._read(addr, 0, 0xFF) for addr in (0x09, 0x08, 0x07, 0x06))

    @hd3_trim.setter
    def hd3_trim(self, values):
        if not isinstance(values, (list, tuple)) or len(values) != 4:
            raise TypeError('values: Expected list / tuple of length 4.')
        if any(not isinstance(i, int) or not 0 <= i <= 255 for i in values):
            raise ValueError('values[i]: Expected integer in range [0, 255].')
        for addr, value in zip((0x09, 0x08, 0x07, 0x06), values):
            self._write(addr, value, 0, 0xFF)

    @property
    def im2_trim(self):
        """Controls the I/Q-channel IM2 trim.

        Returns:
            tuple: integers (i, q) in range [0, 255]
        """
        return tuple(self._read(addr, 0, 0xFF) for addr in (0x05, 0x04))

    @im2_trim.setter
    def im2_trim(self, values):
        if not isinstance(values, (list, tuple)) or len(values) != 2:
            raise TypeError('values: Expected list / tuple of length 2.')
        if any(not isinstance(i, int) or not 0 <= i <= 255 for i in values):
            raise ValueError('values[i]: Expected integer in range [0, 255].')
        for addr, value in zip((0x05, 0x04), values):
            self._write(addr, value, 0, 0xFF)

    @property
    def im3_trim(self):
        """Controls the I/Q-channel IM3 X/Y-vector trim.

        Returns:
            tuple: integers (ix, iy, qx, qy) in range [0, 255]
        """
        return tuple(self._read(addr, 0, 0xFF) for addr in (0x03, 0x02, 0x01, 0x00))

    @im3_trim.setter
    def im3_trim(self, values):
        if not isinstance(values, (list, tuple)) or len(values) != 4:
            raise TypeError('values: Expected list / tuple of length 4.')
        if any(not isinstance(i, int) or not 0 <= i <= 255 for i in values):
            raise ValueError('values[i]: Expected integer in range [0, 255].')
        for addr, value in zip((0x03, 0x02, 0x01, 0x00), values):
            self._write(addr, value, 0, 0xFF)

    @property
    def input_im3_trim(self):
        """RF input IP3 trim. Used to optimize the RF input IP3.

        Returns:
            tuple: integers (cc, ic) in range [0, 3] and [0, 7]
        """
        return self._read(0x11, 0, 0x03), self._read(0x10, 0, 0x07)

    @input_im3_trim.setter
    def input_im3_trim(self, trim):
        if not isinstance(trim, (list, tuple)) or len(trim) != 2:
            raise TypeError('trim: Expected list / tuple of length 2.')
        cc, ic = trim
        if not isinstance(cc, int) or not 0 <= cc <= 3:
            raise ValueError('cc: Expected integer in range [0, 3].')
        if not isinstance(ic, int) or not 0 <= ic <= 7:
            raise ValueError('ic: Expected integer in range [0, 7].')
        self._write(0x11, cc, 0, 0x03)
        self._write(0x10, ic, 0, 0x07)

    @property
    def lo_lf(self):
        """LO matching inductor. Controls the LF1 inductor in the LO matching
        network.

        Returns:
            int: integer in range [0, 3]
        """
        return self._read(0x13, 5, 0x60)

    @lo_lf.setter
    def lo_lf(self, value):
        if not isinstance(value, int) or not 0 <= value <= 3:
            raise ValueError('value: Expected integer in range [0, 3].')
        self._write(0x13, value, 5, 0x60)

    @property
    def lo_vcm(self):
        """LO bias adjust. Used to optimize mixer IP3.

        Returns:
            int: integer in range [0, 7]
        """
        return self._read(0x12, 5, 0xE0)

    @lo_vcm.setter
    def lo_vcm(self, value):
        if not isinstance(value, int) or not 0 <= value <= 7:
            raise ValueError('value: Expected integer in range [0, 7].')
        self._write(0x12, value, 5, 0xE0)

    @property
    def iq_phase_trim(self):
        """IQ phase trim. Controls the IQ phase error over a range from -2.5 to
        2.5 degrees

        Returns:
            int: integer in range [0, 511]
        """
        return (self._read(0x14, 0, 0xFF) << 1) | self._read(0x15, 7, 0x80)

    @iq_phase_trim.setter
    def iq_phase_trim(self, value):
        if not isinstance(value, int) or not 0 <= value <= 511:
            raise ValueError('value: Expected integer in range [0, 511].')
        self._write(0x15, value & 1, 7, 0x80)
        self._write(0x14, value >> 1, 0, 0xFF)

    def reset(self):
        """Reset all registers to their default values."""
        self._write(0x16, 1, 3, 0x08)

    def write(self, address, data):
        """Write to register.

        Args:
            address (int): address
            data (int): data
        """
        self._write(address, data, 0, 0xFF)

    def read(self, address):
        """Read from register.

        Args:
            address (int): address
        """
        return self._read(address, 0, 0xFF)

    def _write(self, address, data, position, mask):
        if not isinstance(address, int) or not 0x0 <= address <= 0x17:
            raise ValueError('address: Expected integer in range [0x0, 0x17].')
        if not isinstance(data, int) or not 0x0 <= data <= 0xFF:
            raise ValueError('data: Expected integer in range [0x0, 0xFF].')
        if not isinstance(position, int) or not 0 <= position <= 7:
            raise ValueError('position: Expected integer in range [0, 7].')
        if not isinstance(mask, int) or not 0x0 <= mask <= 0xFF:
            raise ValueError('mask: Expected integer in range [0x0, 0xFF].')
        data = (data << position) & mask
        if data > 0xFF:
            raise RuntimeError('Data out-of-range.')
        if mask < 0xFF:
            reg_val = self._read(address, 0, 0xFF)
            data |= (reg_val & ~mask & 0xFF)
        wdata = ((address << 8) | data).to_bytes(2, byteorder='big')
        self._iface.write(wdata)

    def _read(self, address, position, mask):
        if not isinstance(address, int) or not 0x0 <= address <= 0x17:
            raise ValueError('address: Expected integer in range [0x0, 0x17].')
        if not isinstance(position, int) or not 0 <= position <= 7:
            raise ValueError('position: Expected integer in range [0, 7].')
        if not isinstance(mask, int) or not 0x0 <= mask <= 0xFF:
            raise ValueError('mask: Expected integer in range [0x0, 0xFF].')
        rdata = self._iface.query((0x80 | address).to_bytes(1, byteorder='big'), 1)
        return (rdata[0] & mask) >> position


class Ltc5586(Ltc5594):

    @property
    def input_select(self):
        """RF switch input select. Controls the RF switch state with a logical
        AND of the RFSW pin.

        Returns:
            int: integer in range [0, 1]
        """
        return self._read(0x17, 0, 0x01)

    @input_select.setter
    def input_select(self, value):
        if not isinstance(value, int) or not 0 <= value <= 1:
            raise ValueError('value: Expected integer in range [0, 1].')
        self._write(0x17, value, 0, 0x01)

    @property
    def atten(self):
        """RF step attenuator.

        Returns:
            float: attenuation in dB
        """
        return float(self._read(0x10, 3, 0xF8))

    @atten.setter
    def atten(self, value):
        if not isinstance(value, (float, int)) or not (0. <= value <= 31.):
            raise TypeError('value: Expected float or integer in range [0, 31] dB.')
        self._write(0x10, int(round(value)), 3, 0xF8)

    @property
    def atten_range(self):
        """Step attenuator range.

        Returns:
            dict: range in dB
        """
        return {'start': 0., 'stop': 31., 'step': 1.}
