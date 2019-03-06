from .block import Block


class Summer(Block):

    @property
    def enable(self):
        """Enable 2nd stage summer.

        Returns:
            bool: enable
        """
        return bool(not self.read(0x0, 0, 0x1))

    @enable.setter
    def enable(self, value):
        if not isinstance(value, bool):
            raise ValueError('value: Expected bool.')
        self.write(0x0, not value, 0, 0x1)
