
"""
write.py - ESP32-S3-GEEK
MicroPython 1.29.0

Texto RGB565 para ST7789.

Fuentes:
    8x8
    10x10
    12x12

Caracteristicas:
- Compatible con la API original.
- Recorte automatico en los 4 bordes.
- Soporte para saltos de linea.
- No escribe fuera de la pantalla.
- No necesita librerias externas.
"""

import display
import font_small
import font_medium
import font_large


def _get_font(size):
    if size == 8:
        return font_small.font_8x8, 8, 8

    if size == 10:
        return font_medium.font_10x10, 10, 10

    if size == 12:
        return font_large.font_12x12, 12, 12

    raise ValueError(
        "Tamaño no soportado. Usa 8, 10 o 12."
    )


def draw_char(x, y, char, color,
              bg_color, size=8):
    """
    Dibuja un caracter con recorte automatico.

    Retorna True si se dibujo alguna parte.
    Retorna False si esta fuera o no existe.
    """

    font, width, height = _get_font(size)

    if char not in font:
        return False

    x = int(x)
    y = int(y)

    screen_w = display.WIDTH
    screen_h = display.HEIGHT

    # Interseccion del caracter con la pantalla.
    x0 = max(0, x)
    y0 = max(0, y)

    x1 = min(screen_w, x + width)
    y1 = min(screen_h, y + height)

    # Completamente fuera de la pantalla.
    if x0 >= x1 or y0 >= y1:
        return False

    visible_w = x1 - x0
    visible_h = y1 - y0

    bitmap = font[char]

    color = int(color) & 0xFFFF
    bg_color = int(bg_color) & 0xFFFF

    # Buffer solo para la zona visible.
    buf = bytearray(
        visible_w * visible_h * 2
    )

    index = 0

    for screen_y in range(y0, y1):
        glyph_y = screen_y - y
        row = bitmap[glyph_y]

        for screen_x in range(x0, x1):
            glyph_x = screen_x - x

            mask = 1 << (
                width - 1 - glyph_x
            )

            if row & mask:
                pixel = color
            else:
                pixel = bg_color

            buf[index] = pixel >> 8
            buf[index + 1] = pixel & 0xFF

            index += 2

    display.set_window_and_write(
        x0,
        y0,
        x1 - 1,
        y1 - 1,
        buf
    )

    return True


def text(x, y, text, color,
         bg_color, size=8):
    """
    Escribe texto usando las fuentes originales.

    El texto que exceda los limites se recorta.

    Soporta:
        - Texto normal
        - Saltos de linea con \\n
        - Coordenadas negativas
        - Rotacion del display

    Mantiene la firma original:
        write.text(x, y, text, color, bg, size)
    """

    _, width, height = _get_font(size)

    start_x = int(x)
    cursor_x = start_x
    cursor_y = int(y)

    for char in str(text):

        if char == "\n":
            cursor_x = start_x
            cursor_y += height
            continue

        if char == "\r":
            cursor_x = start_x
            continue

        # Los caracteres completamente fuera
        # no necesitan enviarse por SPI.
        if (
            cursor_x < display.WIDTH
            and cursor_x + width > 0
            and cursor_y < display.HEIGHT
            and cursor_y + height > 0
        ):
            draw_char(
                cursor_x,
                cursor_y,
                char,
                color,
                bg_color,
                size
            )

        cursor_x += width


def text_width(text, size=8):
    """
    Calcula el ancho en pixeles de la
    linea mas larga.
    """
    _, width, _ = _get_font(size)

    return max(
        len(line) * width
        for line in str(text).split("\n")
    )


def fit_text(text_value, max_width,
             size=8):
    """
    Devuelve el texto truncado para que
    entre en un ancho especifico.

    Ideal para titulos y menus.
    """

    _, width, _ = _get_font(size)

    max_chars = max(
        0,
        int(max_width) // width
    )

    return str(text_value)[:max_chars]

