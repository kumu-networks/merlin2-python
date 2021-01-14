# merlin2-python

## Abstract

merlin2-python is a pure Python driver to control Merlin2-based analog FIR filter boards.

## Dependencies / Installation

merlin2-python has the following dependencies:
* python3 (tested with 3.5-3.7, but any 3.x should work)
* pyftdi
* numpy
* libusb

[Pyftdi's documentation](https://eblot.github.io/pyftdi/installation.html) provides comprehensive
instructions for how to install libusb and pyftdi on any operating system. Follow the instructions
for installing libusb, and then run `pip3 install pyftdi`.

For example, to install `pyftdi` and `numpy` in Ubuntu using `pip`:
``` text
sudo pip3 install numpy pyftdi
```

## Examples

### Basic Usage
Create `Merlin2bEval` object and initialize board.
```python
from merlin2 import Merlin2bEval

dut = Merlin2bEval()
dut.init()
```
Configure board for 2 inputs, 2 outputs, 80 MHz bandwidth, 1700 MHz RF center frequency, no filter chaining.
```python
dut.setup(2, 2, 80e6, 1700e6, chain=False)
```
Write filter weights: organized as a 12 x 4 matrix where each column represents 1 filter of 12 taps. Columns are ordered as (i0o0, i0o1, i1o0, i1o1) where ixoy denotes input `x` and output `y`.
```python
import numpy as np

weights = np.zeros((12, 4))
dut.set_weights(weights)
```
Clear filter weights.
```python
dut.clear_weights()
```
Set input # 0 downmixer gain to 13 dB.
```python
dut.set_downmixer_gain(13.0, input=0)
```
Set input # 0 downmixer DC offset to (0, 0).
```python
dut.set_downmixer_dc_offset(0.0, 0.0, input=0)
```
Set output # 0 DC offset to (0, 0).
```python
dut.set_output_dc_offset(0.0, 0.0, output=0)
```