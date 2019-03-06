from pyftdi.spi import SpiController


class Controller:

    def __init__(self, serial_number=None):
        self._dev = SpiController()
        url = 'ftdi://ftdi:232h/1' if serial_number is None else \
              'ftdi://::{}/1'.format(serial_number)
        self._dev.configure(url)
        self._gpio_port = self._dev.get_gpio()

    def get_gpio(self, pin, direction='input', active_low=False):
        return Gpio(self._gpio_port, pin, direction, active_low)

    def get_spi(self, cs, freq_hz, mode, miso_en_gpio=None):
        port = self._dev.get_port(cs, freq=freq_hz, mode=mode)
        return Spi(port, miso_en_gpio)

    @property
    def serial_number(self):
        return self._dev._ftdi.usb_dev.serial_number


class Gpio:

    def __init__(self, gpio_port, pin, direction, active_low):
        self._gpio_port = gpio_port
        self._mask = 1 << pin
        if direction == 'input':
            self._output = False
        elif direction == 'output':
            self._output = True
        else:
            raise ValueError('direction: Expected \'input\' or \'output\'.')
        if not isinstance(active_low, bool):
            raise TypeError('active_low: Expected bool.')
        self._active_low = active_low
        gpio_mask = self._gpio_port.pins | self._mask
        gpio_dir = self._gpio_port.direction
        gpio_dir |= self._mask if self._output else 0
        self._gpio_port.set_direction(gpio_mask, gpio_dir)

    def set(self, value):
        if not self._output:
            raise RuntimeError('Gpio is not an output, cannot set value' \
                               ' of an input.')
        if not isinstance(value, bool):
            raise TypeError('value: Expected bool.')
        read = self._gpio_port.read(with_output=True)
        if value ^ self._active_low:
            self._gpio_port.write((read & ~self._mask) | self._mask)
        else:
            self._gpio_port.write(read & ~self._mask)

    def get(self):
        return bool(self._gpio_port.read(with_output=True) & self._mask) ^ self._active_low


class Spi:

    def __init__(self, port, miso_en_gpio=None):
        self._port = port
        self.write = port.write
        if miso_en_gpio is None:
            self.read = port.read
            self.query = port.exchange
        else:
            self._miso_en_gpio = miso_en_gpio
            self.read = self._read
            self.query = self._exchange

    def _read(self, *args, **kwargs):
        self._miso_en_gpio.set(True)
        rdata = self._port.read(*args, **kwargs)
        self._miso_en_gpio.set(False)
        return rdata

    def _exchange(self, *args, **kwargs):
        self._miso_en_gpio.set(True)
        rdata = self._port.exchange(*args, **kwargs)
        self._miso_en_gpio.set(False)
        return rdata
