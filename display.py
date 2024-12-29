
from machine import Pin, SPI
import time

# Configuración de SPI y pines
spi = SPI(1, baudrate=40000000, polarity=0, phase=0, sck=Pin(12), mosi=Pin(11))  # SPI optimizado
cs = Pin(10, Pin.OUT)   # Chip Select
dc = Pin(8, Pin.OUT)    # Data/Command
rst = Pin(9, Pin.OUT)   # Reset

# Offset para coordenadas (ajustar según el hardware)
OFFSET_X = 52  # Offset horizontal
OFFSET_Y = 40  # Offset vertical

def write_cmd(cmd):
    """Escribir un comando al controlador del display."""
    cs.value(0)
    dc.value(0)
    spi.write(bytearray([cmd]))
    cs.value(1)

def write_data(data):
    """Escribir datos al controlador del display."""
    cs.value(0)
    dc.value(1)
    spi.write(bytearray([data]))
    cs.value(1)

def init_display():
    """Inicializar el display."""
    rst.value(0)
    time.sleep(0.1)
    rst.value(1)
    time.sleep(0.1)

    write_cmd(0x01)  # Software reset
    time.sleep(0.15)

    write_cmd(0x11)  # Salir del modo de reposo
    time.sleep(0.12)

    write_cmd(0x3A)  # Formato de píxel: RGB565
    write_data(0x55)

    write_cmd(0x36)  # Configuración de memoria
    write_data(0x00)  # Ajuste de orientación
    write_cmd(0x21)  # Inversión de color activada

    write_cmd(0x2A)  # Rango de columnas
    write_data(0x00)
    write_data(0x00)
    write_data(0x00)
    write_data(0xEF)  # 239 columnas

    write_cmd(0x2B)  # Rango de filas
    write_data(0x00)
    write_data(0x00)
    write_data(0x01)
    write_data(0x3F)  # 319 filas

    write_cmd(0x29)  # Encender display

def set_active_window(x0, y0, x1, y1):
    """Configura la ventana activa del display."""
    x0 += OFFSET_X
    x1 += OFFSET_X
    y0 += OFFSET_Y
    y1 += OFFSET_Y
    write_cmd(0x2A)  # Configurar columnas
    write_data(x0 >> 8)
    write_data(x0 & 0xFF)
    write_data(x1 >> 8)
    write_data(x1 & 0xFF)

    write_cmd(0x2B)  # Configurar filas
    write_data(y0 >> 8)
    write_data(y0 & 0xFF)
    write_data(y1 >> 8)
    write_data(y1 & 0xFF)

def set_rotation(rotation):
    """
    Configura la orientación del display.
    :param rotation: 0, 1, 2, o 3 (0: normal, 1: 90°, 2: 180°, 3: 270°)
    """
    madctl_values = [0x00, 0x60, 0xC0, 0xA0]
    if rotation < 0 or rotation > 3:
        raise ValueError("La rotación debe ser 0, 1, 2 o 3")
    
    global _current_rotation
    _current_rotation = rotation  # Guardar la rotación actual

    write_cmd(0x36)  # Comando MADCTL
    write_data(madctl_values[rotation])

    global WIDTH, HEIGHT, OFFSET_X, OFFSET_Y
    if rotation % 2 == 0:
        WIDTH, HEIGHT = 240, 320
        OFFSET_X, OFFSET_Y = 52, 40
    else:
        WIDTH, HEIGHT = 320, 240
        OFFSET_X, OFFSET_Y = 40, 52

def get_rotation():
    """
    Devuelve la rotación actualmente configurada.
    :return: Entero entre 0 y 3 (0: normal, 1: 90°, 2: 180°, 3: 270°)
    """
    return _current_rotation
      

def fill_screen(color):
    """Llena toda la pantalla con un color usando un buffer por líneas."""
    set_active_window(0, 0, 239, 319)  # Toda la pantalla
    write_cmd(0x2C)  # Comando para escribir en memoria

    # Crear un buffer para una línea completa (240 píxeles)
    high_byte = color >> 8
    low_byte = color & 0xFF
    line_buffer = bytearray([high_byte, low_byte] * 240)

    # Enviar el buffer 320 veces (una vez por línea)
    for _ in range(320):
        cs.value(0)
        dc.value(1)
        spi.write(line_buffer)
        cs.value(1)
def set_window_and_write(x_start, y_start, x_end, y_end, data):
    """
    Configura la ventana activa en el display y escribe un bloque de datos.
    :param x_start: Coordenada inicial en X.
    :param y_start: Coordenada inicial en Y.
    :param x_end: Coordenada final en X.
    :param y_end: Coordenada final en Y.
    :param data: Datos en formato RGB565 a escribir en la ventana activa.
    """
    set_active_window(x_start, y_start, x_end, y_end)
    write_cmd(0x2C)  # Comando para iniciar escritura en memoria
    cs.value(0)
    dc.value(1)
    spi.write(data)
    cs.value(1)

