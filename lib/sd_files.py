"""FAT filesystem operations on custom sdspi_raw.SDCardSPI block driver."""
import os
from sdspi_raw import SDCardSPI

class SDStorage:
    def __init__(self, mountpoint='/sd', spi_id=2):
        self.path = mountpoint
        self.card = SDCardSPI(spi_id=spi_id)
        self._mounted = False

    def mount(self):
        if not self._mounted:
            os.mount(os.VfsFat(self.card), self.path)
            self._mounted = True
        return self

    def _path(self, name):
        # Only allow paths relative to the card, no traversal.
        if not isinstance(name, str) or not name or name.startswith('/'):
            raise ValueError('use a nonempty relative filename')
        if any(part in ('', '.', '..') for part in name.split('/')):
            raise ValueError('invalid path component')
        return self.path + '/' + name

    def list(self, name=None):
        return os.listdir(self.path if name is None else self._path(name))

    def read(self, name, binary=False):
        with open(self._path(name), 'rb' if binary else 'r') as file:
            return file.read()

    def write(self, name, data, overwrite=False):
        path = self._path(name)
        if not overwrite:
            try:
                os.stat(path)
            except OSError:
                pass
            else:
                raise OSError('file exists; specify overwrite=True')
        mode = 'wb' if isinstance(data, (bytes, bytearray)) else 'w'
        with open(path, mode) as file:
            file.write(data)

    def delete(self, name):
        os.remove(self._path(name))

    def unmount(self):
        if self._mounted:
            os.umount(self.path)
            self._mounted = False
        self.card.deinit()

