
class Block:

    def __init__(self, ic, offset):
        self._ic = ic
        self._offset = offset

    def write(self, address, *args, **kwargs):
        self._ic.write(address + self._offset, *args, **kwargs)

    def read(self, address, *args, **kwargs):
        return self._ic.read(address + self._offset, *args, **kwargs)
