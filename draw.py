
"""
draw.py - ESP32-S3-GEEK
MicroPython 1.29.0

Primitivas graficas para pantalla ST7789.

Compatible con:
    import draw
    draw.pixel(...)
    draw.line(...)
    draw.rectangle(...)
    draw.circle(...)
    draw.polygon(...)

Tambien permite:
    from draw import Draw
    gfx = Draw()

Sin bibliotecas externas.
"""

import display as _display


class Draw:

    def __init__(self, screen=None):
        self.display = screen if screen is not None else _display

    def _height(self):
        # Compatible con el modulo display.py (HEIGHT)
        # y con una instancia de Display (height).
        h = getattr(self.display, "height", None)
        if h is None:
            h = self.display.HEIGHT
        return int(h)

    def _width(self):
        w = getattr(self.display, "width", None)
        if w is None:
            w = self.display.WIDTH
        return int(w)

    def pixel(self, x, y, color):
        x = int(x)
        y = int(y)

        if 0 <= x < self._width() and 0 <= y < self._height():
            self.display.pixel(x, y, color)

    def _span(self, x0, x1, y, color):
        """Dibuja una linea horizontal recortada."""
        x0 = int(x0)
        x1 = int(x1)
        y = int(y)

        if x0 > x1:
            x0, x1 = x1, x0

        if not (0 <= y < self._height()):
            return

        x0 = max(0, x0)
        x1 = min(self._width() - 1, x1)

        if x0 <= x1:
            self.display.fill_rect(
                x0, y, x1 - x0 + 1, 1, color
            )

    def line(self, x0, y0, x1, y1, color):
        """Dibuja una linea mediante Bresenham."""
        x0 = int(x0)
        y0 = int(y0)
        x1 = int(x1)
        y1 = int(y1)

        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)

        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1

        err = dx + dy

        while True:
            self.pixel(x0, y0, color)

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err

            if e2 >= dy:
                err += dy
                x0 += sx

            if e2 <= dx:
                err += dx
                y0 += sy

    def rectangle(self, x0, y0, x1, y1,
                  color, filled=False):
        """Dibuja un rectangulo vacio o relleno."""
        x0 = int(x0)
        y0 = int(y0)
        x1 = int(x1)
        y1 = int(y1)

        if x0 > x1:
            x0, x1 = x1, x0

        if y0 > y1:
            y0, y1 = y1, y0

        if filled:
            self.display.fill_rect(
                x0,
                y0,
                x1 - x0 + 1,
                y1 - y0 + 1,
                color
            )
        else:
            self._span(x0, x1, y0, color)

            if y1 != y0:
                self._span(x0, x1, y1, color)

            if y1 - y0 >= 2:
                self.display.fill_rect(
                    x0, y0 + 1,
                    1, y1 - y0 - 1,
                    color
                )

                if x1 != x0:
                    self.display.fill_rect(
                        x1, y0 + 1,
                        1, y1 - y0 - 1,
                        color
                    )

    def circle(self, x0, y0, radius,
               color, filled=False):
        """Dibuja un circulo vacio o relleno."""
        x0 = int(x0)
        y0 = int(y0)
        radius = int(radius)

        if radius < 0:
            raise ValueError(
                "El radio no puede ser negativo"
            )

        x = radius
        y = 0
        err = 1 - radius

        while x >= y:

            if filled:
                self._span(
                    x0 - x, x0 + x,
                    y0 + y, color
                )

                if y != 0:
                    self._span(
                        x0 - x, x0 + x,
                        y0 - y, color
                    )

                if x != y:
                    self._span(
                        x0 - y, x0 + y,
                        y0 + x, color
                    )

                    self._span(
                        x0 - y, x0 + y,
                        y0 - x, color
                    )
            else:
                points = (
                    ( x,  y),
                    (-x,  y),
                    ( x, -y),
                    (-x, -y),
                    ( y,  x),
                    (-y,  x),
                    ( y, -x),
                    (-y, -x)
                )

                for dx, dy in points:
                    self.pixel(
                        x0 + dx,
                        y0 + dy,
                        color
                    )

            y += 1

            if err < 0:
                err += 2 * y + 1
            else:
                x -= 1
                err += 2 * (y - x) + 1

    def polygon(self, vertices, color,
                filled=False):
        """Dibuja un poligono vacio o relleno."""

        if len(vertices) < 3:
            raise ValueError(
                "Un poligono necesita 3 vertices"
            )

        pts = [
            (int(x), int(y))
            for x, y in vertices
        ]

        if not filled:
            for i in range(len(pts)):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % len(pts)]

                self.line(
                    x1, y1,
                    x2, y2,
                    color
                )
            return

        # Relleno mediante scanlines.
        # Correccion: obtener altura tanto de
        # display.HEIGHT como de Display.height.

        min_y = max(
            0,
            min(y for x, y in pts)
        )

        max_y = min(
            self._height() - 1,
            max(y for x, y in pts)
        )

        for y in range(min_y, max_y + 1):
            intersections = []

            for i in range(len(pts)):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % len(pts)]

                # Regla semiabierta para no
                # contar dos veces los vertices.
                if ((y1 <= y < y2) or
                        (y2 <= y < y1)):

                    x = (
                        x1
                        + (y - y1) * (x2 - x1)
                        // (y2 - y1)
                    )

                    intersections.append(x)

            intersections.sort()

            for i in range(
                0, len(intersections) - 1, 2
            ):
                self._span(
                    intersections[i],
                    intersections[i + 1],
                    y,
                    color
                )


# -----------------------------------------
# API ORIGINAL
# -----------------------------------------
# Mantiene las llamadas que ya usabas
# en tu repositorio.
# -----------------------------------------

_default = Draw(_display)


def pixel(x, y, color):
    _default.pixel(x, y, color)


def line(x0, y0, x1, y1, color):
    _default.line(
        x0, y0, x1, y1, color
    )


def rectangle(x0, y0, x1, y1,
              color, filled=False):
    _default.rectangle(
        x0, y0, x1, y1,
        color, filled
    )


def circle(x, y, radius,
           color, filled=False):
    _default.circle(
        x, y, radius,
        color, filled
    )


def polygon(color, filled=False, *vertices):
    _default.polygon(
        vertices,
        color,
        filled
    )

