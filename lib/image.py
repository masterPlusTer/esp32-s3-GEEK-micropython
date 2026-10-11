"""Streaming 24-bit uncompressed BMP decoder; original show_bmp API kept."""
import display

def show_bmp(file_path, x_offset=0, y_offset=0):
    with open(file_path, 'rb') as f:
        header = f.read(54)
        if len(header) != 54 or header[:2] != b'BM':
            raise ValueError('invalid BMP header')
        start = int.from_bytes(header[10:14], 'little')
        width = int.from_bytes(header[18:22], 'little')
        raw_h = int.from_bytes(header[22:26], 'little')
        height = raw_h if raw_h < 0x80000000 else raw_h - 0x100000000
        bpp = int.from_bytes(header[28:30], 'little')
        compression = int.from_bytes(header[30:34], 'little')
        if width < 1 or height == 0 or bpp != 24 or compression != 0:
            raise ValueError('only uncompressed 24-bit BMP supported')
        rows = abs(height)
        stride = (width * 3 + 3) & ~3
        # Clip to panel before allocating a row buffer.
        x0 = max(0, x_offset); x1 = min(display.WIDTH, x_offset + width)
        y0 = max(0, y_offset); y1 = min(display.HEIGHT, y_offset + rows)
        if x1 <= x0 or y1 <= y0:
            return
        pixel_row = bytearray((x1-x0)*2)
        for screen_y in range(y0, y1):
            source_y = screen_y - y_offset
            disk_y = source_y if height < 0 else rows-1-source_y
            f.seek(start + disk_y*stride + (x0-x_offset)*3)
            raw = f.read((x1-x0)*3)
            if len(raw) != (x1-x0)*3:
                raise OSError('truncated BMP')
            for ix in range(x1-x0):
                b,g,r = raw[ix*3:ix*3+3]
                rgb = display.rgb565(r,g,b)
                pixel_row[ix*2] = rgb>>8
                pixel_row[ix*2+1] = rgb&255
            display.set_window_and_write(x0, screen_y, x1-1, screen_y, pixel_row)

