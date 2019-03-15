import struct
from time import sleep
from itertools import product
import numpy as np

from ..util import issequence
from .input import Input
from .output import Output
from .filter import Filter
from .delaygroup import DelayGroup
from .summer import Summer


class Merlin2b:

    def __init__(self, interface, reset_gpio, apls_gpio):
        self._iface = interface
        self._resetn_gpio = reset_gpio
        self._apls_gpio = apls_gpio
        self._chained = False
        self.inputs = (
            Input(self, 0x3004),
            Input(self, 0x3014),
        )
        self.delays = (
            DelayGroup(self, 0x4),
            DelayGroup(self, 0x1004),
        )
        self.filters = (
            (Filter(self, 0x38), Filter(self, 0x6C)),
            (Filter(self, 0x1038), Filter(self, 0x106C)),
        )
        self.summers = (
            Summer(self, 0xA0),
            Summer(self, 0x10A0),
        )
        self.outputs = (
            Output(self, 0x3024),
            Output(self, 0x3040),
        )

    def init(self):
        """Initialize device."""
        self.reset()
        if not self.probe():
            raise RuntimeError('Probe failed.')

    def reset(self):
        """Reset IC by toggling RESETN pin."""
        self._apls_gpio.set(False)
        self._resetn_gpio.set(True)
        sleep(1e-3)
        self._resetn_gpio.set(False)
        sleep(1e-3)

    def apply(self):
        """Apply weights by toggling APLS pin."""
        self._apls_gpio.set(True)
        self._apls_gpio.set(False)

    def probe(self):
        """Probe for IC. This will test SPI communication.

        Returns:
            bool: result
        """
        slaves = (0x0, 0x1000, 0x3000)
        magic = (0xABCD0100, 0x12340101, 0x9ABC0103)
        for offset, expected in zip(slaves, magic):
            read = self.read(offset)
            if read != expected:
                return False
        return True

    def setup(self, num_input, num_output, bandwidth, chain=False):
        """Setup IC.

        Args:
            num_input (int): number of inputs, integer in range [1...2]
            num_output (int): number of outputs, integer in range [1...2]
            bandwidth (float): bandwidth in Hz, float in set {20e6, 40e6, 80e6}
            chain (bool, optional): chain multiple filters, default False.
        """
        if not isinstance(num_input, int) or num_input not in (1, 2):
            raise TypeError('num_input: Expected integer in range [1, 2].')
        if not isinstance(num_output, int) or num_output not in (1, 2):
            raise TypeError('num_output: Expected integer in range [1, 2].')
        self.init()
        # Initialize bandgap: toggle enable
        self.write(0x2004, 0x1990E)
        sleep(10e-3)
        self.write(0x2004, 0x1990F)
        # Disable LO in / out
        self.write(0x200C, 0x7)
        for inp in range(2):
            self.delays[inp].input_select = 1 if chain else 0
            self.delays[inp].bandwidth = bandwidth
            self.delays[inp].enable = (inp < num_input or chain,) * 3
            self.delays[inp].rc_cal = 0x10
            self.delays[inp].gains = (0, 0, 0, -2, 0, 0, 0, 0, 0, 0, 0)
            self.inputs[inp].dc_offset = (0., 0.)
            self.inputs[inp].vga_enable = inp < num_input
            self.inputs[inp].vga_gain = 0.
        for inp, out in product(range(2), repeat=2):
            self.filters[inp][out].enable = True
            # i0o1 and i1o0 summer enable and tap_bypass control lines swapped,
            # note that input-output are flipped here.
            self.filters[out][inp].summer_enable = out < num_output
            self.filters[out][inp].tap_bypass = True
        for out in range(2):
            self.summers[out].enable = out < num_output
            self.outputs[out].dc_offset = (0., 0.)
            self.outputs[out].write(0x0, 0x0, 0, 0x3)
        self.clear_weights()
        self._chained = chain

    def set_vga_gain(self, gain, input=None):
        """Set VGA gain.

        Args:
            gain (float): gain setting in range [-2.68, 6.92]
            input (int, optional): integer in range [0, 1]
        """
        if input is None:
            for inp in self.inputs:
                inp.vga_gain = gain
        elif isinstance(input, int) and input in (0, 1):
            self.inputs[input].vga_gain = gain
        else:
            raise TypeError('input: Expected integer in range [0, 1].')

    def get_vga_gain(self, input=None):
        """Get VGA gain.

        Args:
            input (int, optional): integer in range [0, 1]

        Returns:
            tuple or float: tuple of floats or float gain in dB
        """
        if input is None:
            return tuple(inp.vga_gain for inp in self.inputs)
        elif isinstance(input, int) and input in (0, 1):
            return self.inputs[input].vga_gain
        raise TypeError('input: Expected integer in range [0, 1].')

    def get_vga_gain_table(self):
        """VGA gain table.

        Returns:
            tuple: tuple of floats, gain in dB
        """
        return self.inputs[0].vga_gain_table

    def set_gain_profile(self, gains):
        """Set gain-delay profile.

        Args:
            gains (sequence): sequence of gains in dB of length 11 or 22
        """
        expected = 22 if self._chained else 11
        if not issequence(gains) or len(gains) != expected:
            raise TypeError('gains: Expected sequence of floats of length {}.'
                            .format(expected))
        if self._chained:
            self.delays[0].gains = gains[:11]
            self.delays[1].gains = gains[11:]
        else:
            for delays in self.delays:
                delays.gains = gains

    def get_gain_profile(self):
        """Get gain-delay profile.

        Returns:
            tuple: tuple of float gains in dB
        """
        if self._chained:
           return self.delays[0].gains + self.delays[1].gains
        else:
            return self.delays[0].gains

    def set_input_dc_offset(self, i_offset, q_offset, input=None):
        """Set input DC offset.

        Args:
            i_offset (float): I DC offset in range [-1, +1]
            q_offset (float): Q DC offset in range [-1, +1]
            input (int, optional): integer in range [0, 1]

        Returns:
            tuple: length 2 tuple of floats (i, q) in range [-1, +1]
        """
        if input is None:
            for input in range(2):
                self.inputs[input].dc_offset = (i_offset, q_offset)
        elif isinstance(input, int) and input in (0, 1):
            self.inputs[input].dc_offset = (i_offset, q_offset)
        else:
            raise TypeError('input: Expected integer in range [0, 1].')
        return self.inputs[input].dc_offset

    def get_input_dc_offset(self, input):
        """Get input DC offset.

        Args:
            input (int): integer in range [0, 1]

        Returns:
            tuple: length 2 tuple of floats (i, q) in range [-1, +1]
        """
        if not isinstance(input, int) or input not in (0, 1):
            raise TypeError('input: Expected integer in range [0, 1].')
        return self.inputs[input].dc_offset

    def set_output_dc_offset(self, i_offset, q_offset, output=None):
        """Set output DC offset.

        Args:
            i_offset (float): I DC offset in range [-1, +1]
            q_offset (float): Q DC offset in range [-1, +1]
            output (int, optional): integer in range [0, 1]

        Returns:
            tuple: length 2 tuple of floats (i, q) in range [-1, +1]
        """
        if output is None:
            for output in range(2):
                self.outputs[output].dc_offset = (i_offset, q_offset)
        elif isinstance(output, int) and output in (0, 1):
            self.outputs[output].dc_offset = (i_offset, q_offset)
        else:
            raise TypeError('output: Expected integer in range [0, 1].')
        return self.outputs[output].dc_offset

    def get_output_dc_offset(self, output):
        """Get output DC offset.

        Args:
            output (int): integer in range [0, 1]

        Returns:
            tuple: length 2 tuple of floats (i, q) in range [-1, +1]
        """
        if not isinstance(output, int) or output not in (0, 1):
            raise TypeError('output: Expected integer in range [0, 1].')
        return self.outputs[output].dc_offset

    def set_weights(self, weights, apply=True):
        """Set weights.

        Args:
            weights (ndarray): ndarray of shape (12, 4) if not chained, else
                               of shape (23, 2)
            apply (bool, optional): apply weights to filter
        """
        num_taps = 23 if self._chained else 12
        num_filters = 2 if self._chained else 4
        if not isinstance(weights, np.ndarray) or weights.shape != (num_taps, num_filters):
            raise TypeError('weights: Expected ndarray of shape ({}, {}).'
                            .format(num_taps, num_filters))
        fixed = []
        mapped = np.zeros((num_taps, num_filters), dtype=np.complex128)
        for col in range(num_filters):
            data = np.empty((num_taps, 2), dtype=np.int16)
            data[:, 0] = np.round(np.real(weights[:, col]) * 255)
            data[:, 1] = np.round(np.imag(weights[:, col]) * 255)
            fixed.append(data)
            mapped[:, col] = (data[:, 0] / 255) + 1j * (data[:, 1] / 255)
        words = [np.zeros((12, 3), dtype=np.int16) for _ in range(4)]
        if self._chained:
            words[0][:,:2] = fixed[0][:12,:]
            words[2][0,2] = 1 # Disconnect i1o0 tap # 0
            words[2][1:,:2] = fixed[0][12:,:]
            words[1][:,:2] = fixed[1][:12,:]
            words[3][0,2] = 1 # Disconnect i1o1 tap # 0
            words[3][1:,:2] = fixed[1][12:,:]
        else:
            for col in range(4):
                words[col][:,:2] = fixed[col]
        # Handle tap # 11 flip between i0o0 and i0o1
        tmp = words[0][11,:].copy()
        words[0][11,:] = words[1][11,:]
        words[1][11,:] = tmp
        for inp, out in product(range(2), repeat=2):
            self.filters[inp][out].set_weights(words[inp * 2 + out])
        if apply:
            self.apply()
        return mapped

    def get_weights(self):
        """Get weights.

        Returns:
            ndarray: ndarray of shape (12, 4) if not chained, else
                     of shape (23, 2)
        """
        words = []
        for inp, out in product(range(2), repeat=2):
            words.append(self.filters[inp][out].get_weights())
        # Handle tap # 11 flip between i0o0 and i0o1
        tmp = words[0][11,:].copy()
        words[0][11,:] = words[1][11,:]
        words[1][11,:] = tmp
        num_taps = 23 if self._chained else 12
        num_filters = 2 if self._chained else 4
        weights = np.empty((num_taps, num_filters), dtype=np.complex128)
        if self._chained:
            weights[:12,0] = (words[0][:,0] / 255) + 1j * (words[0][:,1] / 255)
            weights[12:,0] = (words[2][1:,0] / 255) + 1j * (words[2][1:,1] / 255)
            weights[:12,1] = (words[1][:,0] / 255) + 1j * (words[1][:,1] / 255)
            weights[12:,1] = (words[3][1:,0] / 255) + 1j * (words[3][1:,1] / 255)
        else:
            for col in range(4):
                weights[:,col] = (words[col][:,0] / 255) + 1j * (words[col][:,1] / 255)
        return weights

    def clear_weights(self, apply=True):
        """Clear weights.

        Args:
            apply (bool, optional): apply weights to filter

        Returns:
            ndarray: ndarray of shape (12, 4) if not chained, else
                     of shape (23, 2)
        """
        num_taps = 23 if self._chained else 12
        num_filters = 2 if self._chained else 4
        weights = np.zeros((num_taps, num_filters), dtype=np.complex128)
        return self.set_weights(weights, apply=apply)

    def write(self, address, data, position=0, mask=2**32-1):
        if not isinstance(address, int) or not 0 <= address <= 0x7FFC \
          or not address % 4 == 0:
            raise TypeError('address: Expected word-aligned integer in range [0, 32768).')
        if not isinstance(data, (list, tuple)):
            data = [data]
        if not all(isinstance(d, int) and 0 <= d < 2**32 for d in data):
            raise TypeError('data: Expected integer in range [0, 2^32).')
        if not isinstance(position, int) or not 0 <= position < 32:
            raise TypeError('position: Expected integer in range [0, 32).')
        if not isinstance(mask, int) or not 0 < mask < 2**32:
            raise TypeError('mask: Expected integer in range [1, 2^32).')
        if mask << position >= 2**32:
            raise ValueError('Invalid mask / position, must be < 2^32.')
        if mask != 2**32 - 1:
            rdata = self.read(address, length=len(data))
            rdata = rdata if len(data) > 1 else [rdata]
            data = [((w << position) & mask) | (r & ~mask) for w, r in zip(data, rdata)]
        write_data = b''.join([(address // 4).to_bytes(2, byteorder='big')] + \
                     [x.to_bytes(4, byteorder='big') for x in data])
        self._iface.write(write_data)

    def read(self, address, position=0, mask=2**32-1, length=1):
        if not isinstance(address, int) or not 0 <= address <= 0x7FFC \
          or not address % 4 == 0:
            raise TypeError('address: Expected word-aligned integer in range [0, 32768).')
        if not isinstance(length, int) or not 0 < length < 8192:
            raise ValueError('length: Expected integer in range [0, 8192).')
        if not isinstance(position, int) or not 0 <= position < 32:
            raise TypeError('position: Expected integer in range [0, 32).')
        if not isinstance(mask, int) or not 0 < mask < 2**32:
            raise TypeError('mask: Expected integer in range [1, 2^32).')
        if mask << position >= 2**32:
            raise ValueError('Invalid mask / position, must be < 2^32.')
        cmd = ((address // 4) | 0x2000).to_bytes(2, byteorder='big')
        data = self._iface.query(cmd, length * 4)
        words = struct.unpack('>{}I'.format(length), data)
        if mask != 2**32 - 1:
            words = [(d & mask) >> position for d in words]
        return words[0] if length == 1 else words
