"""ST7789 for Waveshare ESP32-S3-GEEK, MicroPython, no external drivers.
Backwards-compatible functions and a minimal Display class.
240x135 landscape, 135x240 portrait. RGB565 byte order MSB first.
"""
from machine import Pin, SPI
from time import sleep_ms

spi = SPI(1, baudrate=40_000_000, polarity=0, phase=0,
          sck=Pin(12), mosi=Pin(11))
cs = Pin(10, Pin.OUT, value=1)
dc = Pin(8, Pin.OUT, value=1)
rst = Pin(9, Pin.OUT, value=1)
bl = Pin(7, Pin.OUT, value=1)

# These offsets are typical for ST7789 135x240 panels; adjust if needed.
# Rotation 1 starts in landscape to match the physical board.
_ROTATIONS = (
    (0x00, 135, 240, 52, 40),
    (0x60, 240, 135, 40, 53),
    (0xC0, 135, 240, 53, 40),
    (0xA0, 240, 135, 40, 52),
)
_current_rotation = 1
WIDTH = 240
HEIGHT = 135
OFFSET_X = 40
OFFSET_Y = 53


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def _send(cmd, data=None):
    cs.value(0)
    dc.value(0)
    spi.write(bytes((cmd,)))
    if data is not None:
        dc.value(1)
        spi.write(data)
    cs.value(1)


def write_cmd(cmd):
    _send(cmd)


def write_data(data):
    if isinstance(data, int):
        data = bytes((data & 0xFF,))
    cs.value(0)
    dc.value(1)
    spi.write(data)
    cs.value(1)


def set_rotation(rotation):
    global _current_rotation, WIDTH, HEIGHT, OFFSET_X, OFFSET_Y
    if rotation not in (0, 1, 2, 3):
        raise ValueError('Rotation must be 0, 1, 2 or 3')
    madctl, w, h, ox, oy = _ROTATIONS[rotation]
    _send(0x36, bytes((madctl,)))
    _current_rotation = rotation
    WIDTH, HEIGHT = w, h
    OFFSET_X, OFFSET_Y = ox, oy


def get_rotation():
    return _current_rotation


def init_display(rotation=1):
    bl.value(1)
    rst.value(0)
    sleep_ms(100)
    rst.value(1)
    sleep_ms(120)
    _send(0x01)
    sleep_ms(150)
    _send(0x11)
    sleep_ms(120)
    _send(0x3A, b'\x55')
    _send(0x21)  # Inversion ON for IPS panel
    set_rotation(rotation)
    _send(0x29)
    sleep_ms(20)


def set_active_window(x0, y0, x1, y1):
    if not (0 <= x0 <= x1 < WIDTH and 0 <= y0 <= y1 < HEIGHT):
        raise ValueError('Window outside display: %r' % ((x0, y0, x1, y1),))
    x0 += OFFSET_X
    x1 += OFFSET_X
    y0 += OFFSET_Y
    y1 += OFFSET_Y
    _send(0x2A, bytes((x0 >> 8, x0 & 255, x1 >> 8, x1 & 255)))
    _send(0x2B, bytes((y0 >> 8, y0 & 255, y1 >> 8, y1 & 255)))


def set_window_and_write(x_start, y_start, x_end, y_end, data):
    expected = (x_end - x_start + 1) * (y_end - y_start + 1) * 2
    if len(data) != expected:
        raise ValueError('RGB565 buffer length: expected %d, got %d' % (expected, len(data)))
    set_active_window(x_start, y_start, x_end, y_end)
    _send(0x2C)
    write_data(data)


def fill_screen(color):
    color &= 0xFFFF
    row = bytes((color >> 8, color & 255)) * WIDTH
    set_active_window(0, 0, WIDTH - 1, HEIGHT - 1)
    _send(0x2C)
    cs.value(0)
    dc.value(1)
    for _ in range(HEIGHT):
        spi.write(row)
    cs.value(1)


def pixel(x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        set_window_and_write(x, y, x, y, bytes((color >> 8, color & 255)))


class Display:
    """Convenience facade; the old module-level API remains available."""
    def __init__(self, rotation=1):
        init_display(rotation)

    @property
    def width(self):
        return WIDTH

    @property
    def height(self):
        return HEIGHT

    def fill(self, color):
        fill_screen(color)

    def fill_screen(self, color):
        fill_screen(color)

    def pixel(self, x, y, color):
        pixel(x, y, color)

    def set_rotation(self, rotation):
        set_rotation(rotation)

    def set_window_and_write(self, x0, y0, x1, y1, data):
        set_window_and_write(x0, y0, x1, y1, data)


def fill_rect(x, y, width, height, color):
    """Clipped filled rectangle, supports offscreen coordinates."""
    if width <= 0 or height <= 0:
        return
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(WIDTH, x + width)
    y1 = min(HEIGHT, y + height)
    if x0 >= x1 or y0 >= y1:
        return
    color &= 0xFFFF
    line = bytes((color >> 8, color & 255)) * (x1 - x0)
    set_active_window(x0, y0, x1-1, y1-1)
    _send(0x2C)
    cs.value(0)
    dc.value(1)
    for _ in range(y1-y0):
        spi.write(line)
    cs.value(1)


def deinit():
    """Turn off display and release SPI resources; may be reinitialized later."""
    bl.value(0)
    spi.deinit()


def _display_fill_rect(self, x, y, width, height, color):
    fill_rect(x, y, width, height, color)


def _display_deinit(self):
    deinit()


Display.fill_rect = _display_fill_rect
Display.deinit = _display_deinit

