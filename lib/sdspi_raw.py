"""ESP32-S3-GEEK microSD SPI, read/write block device, no third-party SD driver.

Uses MicroPython machine.SPI/Pin. 512-byte SD sectors, SDSC/SDHC.
Writes with CMD24. Backup the card before testing; untested on physical board.
"""
from machine import Pin, SPI
from time import sleep_ms, ticks_ms, ticks_diff

class SDCardSPI:
    BLOCK_SIZE = 512

    def __init__(self, spi_id=2, baudrate=400000, sck=36, mosi=35, miso=37, cs=34):
        self.spi = SPI(spi_id, baudrate=baudrate, polarity=0, phase=0,
                       sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso))
        self.cs = Pin(cs, Pin.OUT, value=1)
        self._dummy = bytearray([0xff])
        self._cmd = bytearray(6)
        self._buf = bytearray(1)
        self.high_capacity = False
        self.sectors = 0
        self._init_card()

    def _clock(self, n):
        for _ in range(n):
            self.spi.write(self._dummy)

    def _readbyte(self):
        self.spi.readinto(self._buf, 0xff)
        return self._buf[0]

    def _select(self):
        self.cs(0)
        self._readbyte()

    def _release(self):
        self.cs(1)
        self._readbyte()

    def _command(self, cmd, arg=0, crc=0x01, keep=False):
        self._select()
        c = self._cmd
        c[0] = 0x40 | cmd
        c[1] = (arg >> 24) & 0xff
        c[2] = (arg >> 16) & 0xff
        c[3] = (arg >> 8) & 0xff
        c[4] = arg & 0xff
        c[5] = crc
        self.spi.write(c)
        result = 0xff
        for _ in range(16):
            result = self._readbyte()
            if not result & 0x80:
                break
        if not keep:
            self._release()
        return result

    def _cmd_r3r7(self, cmd, arg=0, crc=0x01):
        self._select()
        c = self._cmd
        c[0] = 0x40 | cmd
        c[1] = (arg >> 24) & 255
        c[2] = (arg >> 16) & 255
        c[3] = (arg >> 8) & 255
        c[4] = arg & 255
        c[5] = crc
        self.spi.write(c)
        r = 255
        for _ in range(16):
            r = self._readbyte()
            if not r & 0x80:
                break
        payload = bytearray(4)
        if r != 255:
            self.spi.readinto(payload, 0xff)
        self._release()
        return r, payload

    def _appcmd(self, cmd, arg=0):
        r = self._command(55)
        if r not in (0, 1):
            return r
        return self._command(cmd, arg)

    def _read_data(self, buf):
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < 500:
            token = self._readbyte()
            if token == 0xfe:
                self.spi.readinto(buf, 0xff)
                self._readbyte()  # CRC high
                self._readbyte()  # CRC low
                return
            if token != 0xff:
                raise OSError('SD unexpected token 0x%02x' % token)
        raise OSError('SD read timeout waiting for data token')

    def _init_card(self):
        self.cs(1)
        self._clock(12)  # >= 74 clocks with CS high
        deadline = ticks_ms()
        while ticks_diff(ticks_ms(), deadline) < 1000:
            if self._command(0, 0, 0x95) == 1:
                break
            sleep_ms(10)
        else:
            raise OSError('SD CMD0 failed: check card/pins/power')

        r, response = self._cmd_r3r7(8, 0x1aa, 0x87)
        if r == 1:
            if response[2] != 1 or response[3] != 0xaa:
                raise OSError('SD CMD8 voltage/check pattern mismatch')
            v2 = True
        elif r == 5:  # illegal command: older SDSC
            v2 = False
        else:
            raise OSError('SD CMD8 unexpected response 0x%02x' % r)

        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < 3000:
            r = self._appcmd(41, 0x40000000 if v2 else 0)
            if r == 0:
                break
            if r != 1:
                raise OSError('SD ACMD41 response 0x%02x' % r)
            sleep_ms(20)
        else:
            raise OSError('SD ACMD41 initialization timeout')

        r, ocr = self._cmd_r3r7(58)
        if r != 0:
            raise OSError('SD CMD58 response 0x%02x' % r)
        self.high_capacity = v2 and bool(ocr[0] & 0x40)
        if not self.high_capacity and self._command(16, 512) != 0:
            raise OSError('SD CMD16 block length failed')
        self.sectors = self._read_capacity()
        # Raise transfer speed only after initialization.
        self.spi.init(baudrate=4_000_000, polarity=0, phase=0)

    def _read_capacity(self):
        if self._command(9, keep=True) != 0:
            self._release()
            raise OSError('SD CMD9 failed')
        csd = bytearray(16)
        try:
            self._read_data(csd)
        finally:
            self._release()
        version = (csd[0] >> 6) & 3
        if version == 1:
            csize = ((csd[7] & 63) << 16) | (csd[8] << 8) | csd[9]
            return (csize + 1) * 1024
        if version == 0:
            read_bl_len = csd[5] & 15
            csize = ((csd[6] & 3) << 10) | (csd[7] << 2) | (csd[8] >> 6)
            cmult = ((csd[9] & 3) << 1) | (csd[10] >> 7)
            return ((csize + 1) << (cmult + 2)) * (1 << read_bl_len) // 512
        raise OSError('Unsupported CSD structure')

    def readblocks(self, block, buf, offset=0):
        if block < 0 or len(buf) % 512:
            raise ValueError('readblocks requires whole 512-byte sectors')
        if block + len(buf)//512 > self.sectors:
            raise ValueError('sector out of bounds')
        # optional offset is in bytes for MicroPython extended block protocol
        if offset:
            raise ValueError('partial-sector reads not supported')
        view = memoryview(buf)
        for i in range(len(buf)//512):
            sector = block + i
            addr = sector if self.high_capacity else sector * 512
            r = self._command(17, addr, keep=True)
            if r != 0:
                self._release()
                raise OSError('SD CMD17 response 0x%02x' % r)
            try:
                self._read_data(view[i*512:(i+1)*512])
            finally:
                self._release()
        return 0

    def _wait_ready(self, timeout_ms=1500):
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < timeout_ms:
            if self._readbyte() == 0xff:
                return
        raise OSError('SD busy timeout')

    def writeblocks(self, block, buf, offset=0):
        if offset:
            raise ValueError('partial-sector writes unsupported')
        if block < 0 or len(buf) % 512:
            raise ValueError('writeblocks requires whole 512-byte sectors')
        count = len(buf) // 512
        if block + count > self.sectors:
            raise ValueError('sector out of bounds')
        view = memoryview(buf)
        for i in range(count):
            sector = block + i
            addr = sector if self.high_capacity else sector * 512
            r = self._command(24, addr, keep=True)
            if r != 0:
                self._release()
                raise OSError('SD CMD24 response 0x%02x' % r)
            try:
                self._readbyte()  # Nwr before data token
                self.spi.write(b'\xfe')
                self.spi.write(view[i*512:(i+1)*512])
                self.spi.write(b'\xff\xff')  # dummy CRC with CRC disabled
                response = self._readbyte() & 0x1f
                if response != 0x05:
                    raise OSError('SD write rejected, token 0x%02x' % response)
                self._wait_ready()
            finally:
                self._release()
        return 0

    def ioctl(self, op, arg):
        if op in (4,):  # block count
            return self.sectors
        if op == 5:     # block size
            return 512
        if op in (1, 2, 3):  # init, deinit, sync
            return 0
        if op == 6:  # erase not implemented, FAT can still delete files
            return -1
        return 0

    def deinit(self):
        self.cs(1)
        self.spi.deinit()

